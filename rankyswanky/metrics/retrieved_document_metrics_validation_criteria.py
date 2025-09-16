"""
Script for finding what different requirements is for answering a question based on many parameters.

The rewritten questions will be used to determine what a good answer would be for different roles.
The purpose is to make questions specific such that implicit needs for the user of what the want by the question is met.
"""
import os
import re
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
import json
from genson import SchemaBuilder
from typing import Any, Dict
from rankyswanky.metrics.abstract_retrieved_document_metrics import RelevanceEvaluatorBase


from experimentation.calc_gain_gen_and_eval_question_parameters.grundfos_perspective import Perspective, perspectives
from rankyswanky.models.caching_models import GenAndEvaluateQuestionParameters
from rankyswanky.models.retrieval_evaluation_models import RetrievedDocumentMetrics
from rankyswanky.persistence import mapper_domain_to_caching_models, pydantic_caching

class RewrittenAnswersStructuredOutput(BaseModel):
    rewritten_questions: list[str] = Field(
        default_factory=list,
        description="List of rewritten questions based on the original question and perspective."
    )

class RewrittenQuestions(RewrittenAnswersStructuredOutput):
    """Model to hold rewritten questions."""
    question: str = Field(..., description="The original question.")
    perspective: str = Field(
        ..., description="The perspective from which the question is asked."
    )

class PropertiesOfCorrectAnswerStructuredOutput(BaseModel):
    """Model to hold properties of a correct answer."""
    properties_of_a_good_document_containing_all_perspectives: list[str] = Field(
        default_factory=list,
        description="List of properties that a correct answer should have."
    )

class CombinedOutput(RewrittenQuestions, PropertiesOfCorrectAnswerStructuredOutput):
    """Final model combining rewritten questions and properties of a correct answer."""
    pass

class EvaluatedValidationCriterias(BaseModel):
    """Model to hold evaluated validation criteria."""
    evaluation: Dict[str, bool]

    def __len__(self) -> int:
        """Return the number of validation criteria."""
        return len(self.evaluation)

    def count_validation_criterias_met(self) -> int:
        """Count how many validation criteria are met."""
        return sum(1 for met in self.evaluation.values() if met)

    def summary(self) -> str:
        """Summarize the evaluation results."""
        total = len(self.evaluation)
        met = self.count_validation_criterias_met()
        return f"Validation Criteria Met: {met}/{total}"



def _generate_perspective_rewritten_questions(
    question: str,
    perspective: str,
    llm: BaseChatModel,
) -> RewrittenQuestions:
    """Get rewritten questions from the LLM based on the original question and perspective."""
    prompt: str = (
        f"Rewrite the following question to be specific and actionable for the given perspective.\n"
        f"Original Question: {question}\n"
        f"Perspective:\n{perspective}\n"
        f"Return a list of 3 rewritten questions, each tailored to the perspective."
    )
    response = llm.with_structured_output(
        RewrittenAnswersStructuredOutput,
    ).invoke(prompt)
    assert isinstance(response, RewrittenAnswersStructuredOutput)
    return RewrittenQuestions(
        question=question,
        perspective=perspective,
        rewritten_questions=response.rewritten_questions,
    )

def _generate_validation_criterias(
    question: str,
    rewritten_questions: list[str],
    llm: BaseChatModel,
) -> PropertiesOfCorrectAnswerStructuredOutput:
    """Get properties of a correct answer from the LLM using the original and rewritten questions for inspiration."""
    # prompt1: str = (
    #     f"Given the following original question and perspective, list the key validation questions that information that documentation should contain for enabling a service representative to write a good answer.\n"
    #     f"Do not include any generic validation questions, only specific validation questions that are relevant to the question and different perspective the user might have.\n"
    #     f"Never combine multiple questions into a single validation question, split them into multiple validation questions if needed.\n"
    #     f"Original Question: {question}\n"
    #     f"Rewritten Questions (for inspiration to understand different reasons why the question might be asked):\n"
    #     f"{chr(10).join(f'- {rq}' for rq in rewritten_questions)}\n"
    #     f"Return a list of validation questions that a good answer should fulfill. They should be formulated as true/false boolean questions that can be used to evaluate the documentation."
    # )
    prompt2: str = (
        f"Given the following original question and perspective, list the key properties that the documentation should have to enable a service representative to write a good answer.\n"
        f"Ensure that each property is expressed as a short sentence beginning with 'It ' followed by an active verb.\n"
        f"Focus on specific properties relevant to the question and the different perspectives the user might have.\n"
        f"Avoid including generic properties; instead, specify ones that are directly related to the context.\n"
        f"Do not combine multiple things to validate into a single statement; instead list each property individually as simple statements. There should only be a single thing to validate for the service representative at a time such it is easy to evaluate.\n"
        f"Original Question: {question}\n"
        f"Rewritten Questions (for inspiration to understand different reasons why the question might be asked):\n"
        f"{chr(10).join(f'- {rq}' for rq in rewritten_questions)}\n"
        f"Return a list of properties that a good answer should embody. Each property should be formulated as a sentence starting with 'It,' using active voice to guide the evaluation of the documentation."
    )
    response = llm.with_structured_output(
        PropertiesOfCorrectAnswerStructuredOutput,
    ).invoke(prompt2)
    assert isinstance(response, PropertiesOfCorrectAnswerStructuredOutput)
    return response

def _sanitize_property_name(prop: str) -> str:
    """Sanitize property name to be JSON schema compatible (alphanumeric, _, -)."""
    sanitized: str = prop.strip().strip(".")
    # Remove commas
    sanitized = sanitized.replace(",", "")
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    # Remove ' and "
    sanitized = sanitized.replace("'", "").replace('"', "")
    # Replace any other non-alphanumeric characters
    sanitized: str = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)
    # # Ensure it doesn't start with a digit
    # if sanitized and sanitized[0].isdigit():
    #     sanitized = f"p_{sanitized}"
    # # Optionally, truncate if too long (e.g., 64 chars)
    # sanitized = sanitized[:64]
    return sanitized

def _create_validation_model(
    sanitized_properties: list[str],
    question: str,
) -> dict[str, Any]:
    """Create a json schema model for the validation properties."""
    builder = SchemaBuilder()
    builder.add_schema({"type": "object", "properties": {},
                        "title": "ValidationProperties",
                        "description": f"Validation properties for validating if documents is suited for answering the question: {question}"})
    for prop in sanitized_properties:
        builder.add_object({prop: False})
    
    return builder.to_schema()


def _evaluate_document_properties(
    question: str,
    properties: list[str],
    document: str,
    llm: BaseChatModel,
) -> EvaluatedValidationCriterias:
    """Generate the booleans for the validation properties based on the document."""
    property_sanitized_lookup: Dict[str, str] = {
        _sanitize_property_name(prop): prop for prop in properties
    }
    json_schema = _create_validation_model(
        sanitized_properties=list(property_sanitized_lookup.keys()),
        question=question,
    )
    prompt: str = (
        f"Given the following document and properties, evaluate the document against the properties.\n"
        f"Document:\n{document}\n"
        f"Properties:\n{chr(10).join(f'- {prop}' for prop in properties)}\n"
        f"Return a JSON object with boolean values for each property, indicating whether the document fulfills the property.\n"
    )
    response = llm.with_structured_output(json_schema).invoke(prompt)
    return EvaluatedValidationCriterias(
        evaluation=response,
    )



class RelevanceEvaluator(RelevanceEvaluatorBase):
    """Evaluates the relevance of retrieved documents for a given query."""
    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm
        self.reset()

    def reset(self) -> None:
        self._question = ""
        self._validation_criteria: CombinedOutput | None = None
        self._validation_criterias_met_history: Dict[str, bool] = {}

    def set_question(self, question: str) -> None:
        self.reset()
        self._question = question
        self._extract_validation_criterias(question, perspectives[0].to_repr_relevant_to_rewrite(), self._llm)
        self._validation_criterias_met_history = {validation_criteria: False for validation_criteria in self._validation_criteria.properties_of_a_good_document_containing_all_perspectives}


    def _extract_validation_criterias(
        self,
        question: str,
        perspective: str,
        llm: BaseChatModel,
    ) -> None:
        """
        Get combined output of rewritten questions and properties of a correct answer.
        """
        rewritten_questions = _generate_perspective_rewritten_questions(question, perspective, llm)
        properties = _generate_validation_criterias(
            question, rewritten_questions.rewritten_questions, llm
        )
        self._validation_criteria = CombinedOutput(
            question=rewritten_questions.question,
            perspective=rewritten_questions.perspective,
            rewritten_questions=rewritten_questions.rewritten_questions,
            properties_of_a_good_document_containing_all_perspectives=properties.properties_of_a_good_document_containing_all_perspectives,
        )

    def create_retrieved_document_metrics(self, context: str) -> RetrievedDocumentMetrics | None:
        """Calculates the relevance score of a document based on the question."""
        if not self._validation_criteria:
            return None
        evaluated_criteria = _evaluate_document_properties(
            question=self._question,
            properties=self._validation_criteria.properties_of_a_good_document_containing_all_perspectives,
            document=context,
            llm=self._llm,
        )
        relevance = evaluated_criteria.count_validation_criterias_met() / len(evaluated_criteria)
        novelty = self._calculate_novelty(evaluated_criteria)
        self._update_validation_criterias_met_history(evaluated_criteria)
        return RetrievedDocumentMetrics(relevance=relevance, novelty=novelty if novelty is not None else 0.0,)

    def _calculate_novelty(self, evaluated_criteria: EvaluatedValidationCriterias) -> float | None:
        """
        Calculates how big a percentage of the met validation criteria are met for the first time.

        novelty = newly met validation criteria / met validation criteria by module
        """
        if not evaluated_criteria:
            return None
        if not self._validation_criteria:
            return None
        count_of_met_criteria: int = 0
        newly_met_criteria_count: int = 0
        for prop, met in evaluated_criteria.evaluation.items():
            if met:
                count_of_met_criteria += 1
                if not self._validation_criterias_met_history.get(prop, False):
                    newly_met_criteria_count += 1
        return newly_met_criteria_count / count_of_met_criteria if count_of_met_criteria > 0 else 0

    def _update_validation_criterias_met_history(self, evaluated_criteria: EvaluatedValidationCriterias) -> None:
        """Updates the history of validation criterias met."""
        for prop, met in evaluated_criteria.evaluation.items():
            if met:
                self._validation_criterias_met_history[prop] = True


class RelevanceEvaluatorWithPersistance(RelevanceEvaluator):
    def _load_cache(self, question: str, perspective: str) -> CombinedOutput | None:
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=GenAndEvaluateQuestionParameters,
            primary_key_value=mapper_domain_to_caching_models.default_gen_eval_id_strategy(query_id=mapper_domain_to_caching_models.default_query_id_strategy(question),perspective_id=mapper_domain_to_caching_models.default_perspective_id_strategy(perspectives[0].to_repr_relevant_to_rewrite()))
        )
        if not persisted_model:
            return None
        return CombinedOutput(
            question=question,
            perspective="",
            rewritten_questions=persisted_model.rewritten_questions,
            properties_of_a_good_document_containing_all_perspectives=persisted_model.properties_of_a_good_document_containing_all_perspectives,
        )

    def _save_cache(self, question: str, perspective: str, model: CombinedOutput) -> None:
        persistence_obj = mapper_domain_to_caching_models.map_combined_output_to_gen_and_evaluate_params(self._validation_criteria)
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])

    def _extract_validation_criterias(self, question: str, perspective: str, llm: BaseChatModel) -> None:
        """
        Get combined output of rewritten questions and properties of a correct answer.
        """
        # TODO: Figure out how to move the caching logic and all persistance function to a separate module (separation of concerns)
        persisted_model = self._load_cache(question=question, perspective=perspective)
        if persisted_model:
            self._validation_criteria = CombinedOutput(
                question=question,
                perspective="",
                rewritten_questions=persisted_model.rewritten_questions,
                properties_of_a_good_document_containing_all_perspectives=persisted_model.properties_of_a_good_document_containing_all_perspectives,
            )
        else:
            super()._extract_validation_criterias(question, perspective, llm)
            self._save_cache(question=question, perspective=perspective, model=self._validation_criteria)


if __name__ == "__main__":
    from rankyswanky.adapters import llm
    def main(questions: list[str], documents: list[str]) -> None:
        """Main function to run the script using RelevanceEvaluator."""
        for question in questions:
            for perspective in perspectives:
                evaluator = RelevanceEvaluator(llm=llm.open_chat_llm)
                evaluator.set_question(question)
                print(f"Original Question: {question}")
                print("Rewritten Questions:")
                for rq in evaluator._validation_criteria.rewritten_questions:
                    print(f"- {rq}")
                print("Properties of a Good Document:")
                for prop in evaluator._validation_criteria.properties_of_a_good_document_containing_all_perspectives:
                    print(f"- {prop}")
                print("\n" + "="*50 + "\n")
                for document in documents:
                    metrics = evaluator.create_retrieved_document_metrics(document)
                    if metrics is not None:
                        print(f"Evaluation for Document:\n{document}\nResult: {metrics}\n")
                        print(f"Relevance: {metrics.relevance:.2f}, Novelty: {metrics.novelty:.2f}")
                    else:
                        print("Could not evaluate document metrics.")
                    print("\n" + "="*50 + "\n")

    questions = [
        "what is an E-pump?",
        "What is the advantages of IE5 motors?",
        "Help me explain the TPE product range to my customer.",
    ]
    documents = [
        "---\nSource title: CRE, CRIE, CRNE (Data booklet)\nBreadcrumbs: CRE, CRIE, CRNE\n---\n\n## Components of a Grundfos E-pump\n\nAn E-pump is not just a pump, but a system which is able to solve application problems or save energy in a variety of pump installations. All that is required is the power supply connection and the fitting of the E-pump in the pipe system, and the pump is ready for operation. The pump has been tested and pre-configured from the factory. The operator only has to specify the desired setpoint (pressure) and the system is operational.\n\nTM030431\n\n",
        "---\nSource title: CRE, CRIE, CRNE (Data booklet)\nBreadcrumbs: Control of E-pumps\n---\n\n## Control options\n\nIt is possible to communicate with E-pumps via the following platforms:\n\n* the operating panel on the pump\n* Grundfos GO\n* Grundfos GO Link\n* the central management system.\nThe purpose of controlling an E-pump is to monitor and control the pressure, temperature, flow rate and liquid level of the system.\n\n",
        "---\nSource title: CME, CM (Data booklet)\nBreadcrumbs: The pump uses the input from the sensor to control the differential temperature.\n  / Constant flow rate / Constant flow rate / Control of E-pumps\n---\n\n##### Control options\n\nIt is possible to communicate with E-pumps via the following platforms:\n\n* the operating panel on the pump\n* Grundfos GO\n* Grundfos GO Link\n* the central management system.\nThe purpose of controlling an E-pump is to monitor and control the pressure, temperature, flow rate and liquid level of the system.\n\n",
    ]
    main(questions, documents)