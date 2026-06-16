"""
Script for finding what different requirements is for answering a question based on many parameters.

The rewritten questions will be used to determine what a good answer would be for different roles.
The purpose is to make questions specific such that implicit needs for the user of what the want by the question is met.
"""
import re
from genson import SchemaBuilder
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field
from rankyswanky.application.cache_aware_evaluation_coordinator import (
    CacheAwareEvaluationCoordinator,
)
from rankyswanky.application.metrics.abstract_retrieved_document_metrics import RelevanceEvaluatorBase
from rankyswanky.models.metric_calculation_models import (
    QuestionWithRewrites,
    QuestionWithRewritesAndCorrectnessProps,
    RetrievedDocumentStatistics,
    WeightedProperty,
)
from rankyswanky.models.retrieval_evaluation_models import RetrievedDocumentMetrics
from typing import Any


class RewrittenAnswersStructuredOutput(BaseModel):
    """Output class to be used for LLM structured output."""

    rewritten_questions: list[str] = Field(
        default_factory=list,
        description="List of rewritten questions based on the original question and perspective.",
    )


class WeightedPropertyStructuredOutput(BaseModel):
    """Single validation property with an associated importance weight."""

    name: str = Field(
        default="",
        description="Name of the validation property as a short sentence.",
    )
    weight: float = Field(
        default=1.0,
        description="Positive importance weight for this property.",
        gt=0,
    )


class PropertiesOfCorrectAnswerStructuredOutput(BaseModel):
    """Output class to be used for LLM structured output."""

    properties: list[WeightedPropertyStructuredOutput] = Field(
        default_factory=list,
        description="List of weighted properties that a correct answer should have.",
    )


class EvaluatedValidationCriterias(BaseModel):
    """Model to hold evaluated validation criteria."""

    evaluation: dict[str, bool]

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
) -> QuestionWithRewrites:
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
    return QuestionWithRewrites(
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
        f"Return a properties list where each item has: "
        f"name (the property sentence starting with 'It' in active voice) and "
        f"weight (a positive number indicating how critical that property is for answering the question)."
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
    sanitized: str = re.sub(r"[^a-zA-Z0-9_-]", "_", sanitized)
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
    property_sanitized_lookup: dict[str, str] = {
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

    def __init__(
        self,
        llm: BaseChatModel,
        cache_coordinator: CacheAwareEvaluationCoordinator,
        perspective: str,
    ) -> None:
        self._llm = llm
        self._cache_coordinator = cache_coordinator
        self._perspective = perspective
        self.reset()

    def reset(self) -> None:
        self._question = ""
        self._validation_criteria: QuestionWithRewritesAndCorrectnessProps | None = None
        self._validation_criterias_met_history: dict[str, int] = {}

    def set_question(self, question: str) -> None:
        self.reset()
        self._question = question
        self._validation_criteria = self._cache_coordinator.prepare_question_context(
            question=question,
            perspective=self._perspective,
            compute_criteria_fn=lambda q, p: self._extract_validation_criterias(q, p, self._llm),
        )
        self._validation_criterias_met_history = dict.fromkeys(
            (
                _sanitize_property_name(prop.name)
                for prop in self._validation_criteria.weighted_properties
            ),
            0,
        )

    def _extract_validation_criterias(
        self,
        question: str,
        perspective: str,
        llm: BaseChatModel,
    ) -> QuestionWithRewritesAndCorrectnessProps:
        """
        Get combined output of rewritten questions and properties of a correct answer.
        """
        rewritten_questions = _generate_perspective_rewritten_questions(question, perspective, llm)
        properties = _generate_validation_criterias(
            question, rewritten_questions.rewritten_questions, llm,
        )
        weighted_properties = [
            WeightedProperty(name=prop.name, weight=prop.weight)
            for prop in properties.properties
            if prop.name.strip()
        ]
        normalized_weighted_properties = self._normalize_weighted_properties(
            weighted_properties,
        )
        return QuestionWithRewritesAndCorrectnessProps(
            question=rewritten_questions.question,
            perspective=rewritten_questions.perspective,
            rewritten_questions=rewritten_questions.rewritten_questions,
            weighted_properties=normalized_weighted_properties,
        )
    def _calculate_document_statistics_and_relevance(self, document_content: str) -> RetrievedDocumentStatistics:
        """Calculates the relevance score of a document based on the question."""
        if not self._validation_criteria:
            raise ValueError("Validation criteria not set. Call set_question() first.")
        return self._cache_coordinator.get_or_create_document_evaluation(
            question=self._question,
            perspective=self._perspective,
            document_content=document_content,
            compute_fn=lambda q, _p, d: self._compute_document_statistics(q, d),
        )

    def _compute_document_statistics(
        self,
        question: str,
        document_content: str,
    ) -> RetrievedDocumentStatistics:
        """Compute document statistics without any cache logic."""
        if not self._validation_criteria:
            raise ValueError("Validation criteria not set. Call set_question() first.")
        evaluated_criteria = _evaluate_document_properties(
            question=question,
            properties=[
                prop.name for prop in self._validation_criteria.weighted_properties
            ],
            document=document_content,
            llm=self._llm,
        )
        relevance = evaluated_criteria.count_validation_criterias_met() / len(evaluated_criteria)
        return RetrievedDocumentStatistics(
            relevance=relevance,
            evaluated_properties_of_a_good_document=evaluated_criteria.evaluation,
        )

    def create_retrieved_document_metrics(self, document_content: str) -> RetrievedDocumentMetrics:
        """Calculates the relevance score of a document based on the question."""
        if not self._validation_criteria:
            raise ValueError("Validation criteria not set. Call set_question() first.")
        retrieved_document_stats = self._calculate_document_statistics_and_relevance(document_content)
        novelty = self._calculate_novelty(retrieved_document_stats.evaluated_properties_of_a_good_document)
        self._update_validation_criterias_met_history(retrieved_document_stats.evaluated_properties_of_a_good_document)
        return RetrievedDocumentMetrics(relevance=retrieved_document_stats.relevance, novelty=novelty if novelty is not None else 0.0)

    def _calculate_novelty(self, evaluated_criteria: dict[str, bool]) -> float:
        """
        Importance-weighted novelty decay model.

        For each dimension i covered by the document:
            novelty_i = 1 / (1 + coverage_i^alpha * importance_i)
        novelty_doc = sum(importance_i * novelty_i for covered dimensions)

        Novelty is bounded (0, 1], never drops to zero, and is 1 when all
        dimensions are covered for the first time by a perfectly relevant document.
        """
        if not evaluated_criteria:
            raise ValueError("No evaluated criteria provided.")
        if not self._validation_criteria:
            raise ValueError("Validation criteria not set. Call set_question() first.")
        normalized_weighted_properties = self._normalize_weighted_properties(
            self._validation_criteria.weighted_properties,
        )
        novelty_doc: float = 0.0
        for prop in normalized_weighted_properties:
            sanitized_prop = _sanitize_property_name(prop.name)
            importance_i = prop.weight
            if evaluated_criteria.get(sanitized_prop, False):
                coverage_i: int = self._validation_criterias_met_history.get(sanitized_prop, 0)
                novelty_i: float = 1.0 / (1.0 + (coverage_i ** 1.0) * importance_i)
                novelty_doc += importance_i * novelty_i
        return novelty_doc

    def _update_validation_criterias_met_history(self, evaluated_criteria: dict[str, bool]) -> None:
        """Increments the coverage count for each dimension met by the current document."""
        for prop, met in evaluated_criteria.items():
            if met:
                self._validation_criterias_met_history[prop] = self._validation_criterias_met_history.get(prop, 0) + 1

    @staticmethod
    def _normalize_weighted_properties(
        weighted_properties: list[WeightedProperty],
    ) -> list[WeightedProperty]:
        """Normalize weights so they sum to 1 while preserving property order."""
        if not weighted_properties:
            return []
        total_weight = sum(prop.weight for prop in weighted_properties) or 1.0
        return [
            WeightedProperty(name=prop.name, weight=prop.weight / total_weight)
            for prop in weighted_properties
        ]

# if __name__ == "__main__":
#     from rankyswanky.adapters import llm
#     def main(questions: list[str], documents: list[str]) -> None:
#         """Main function to run the script using RelevanceEvaluator."""
#         for question in questions:
#             for perspective in perspectives:
#                 evaluator = RelevanceEvaluator(llm=llm.chat_llm)
#                 evaluator.set_question(question)
#                 print(f"Original Question: {question}")
#                 print("Rewritten Questions:")
#                 for rq in evaluator._validation_criteria.rewritten_questions:
#                     print(f"- {rq}")
#                 print("Properties of a Good Document:")
#                 for prop in evaluator._validation_criteria.weighted_properties:
#                     print(f"- {prop.name} (weight={prop.weight})")
#                 print("\n" + "="*50 + "\n")
#                 for document in documents:
#                     metrics = evaluator.create_retrieved_document_metrics(document)
#                     if metrics is not None:
#                         print(f"Evaluation for Document:\n{document}\nResult: {metrics}\n")
#                         print(f"Relevance: {metrics.relevance:.2f}, Novelty: {metrics.novelty:.2f}")
#                     else:
#                         print("Could not evaluate document metrics.")
#                     print("\n" + "="*50 + "\n")

#     questions = [
#         "what is an E-pump?",
#         "What is the advantages of IE5 motors?",
#         "Help me explain the TPE product range to my customer.",
#     ]
#     documents = [
#         "---\nSource title: CRE, CRIE, CRNE (Data booklet)\nBreadcrumbs: CRE, CRIE, CRNE\n---\n\n## Components of a Grundfos E-pump\n\nAn E-pump is not just a pump, but a system which is able to solve application problems or save energy in a variety of pump installations. All that is required is the power supply connection and the fitting of the E-pump in the pipe system, and the pump is ready for operation. The pump has been tested and pre-configured from the factory. The operator only has to specify the desired setpoint (pressure) and the system is operational.\n\nTM030431\n\n",
#         "---\nSource title: CRE, CRIE, CRNE (Data booklet)\nBreadcrumbs: Control of E-pumps\n---\n\n## Control options\n\nIt is possible to communicate with E-pumps via the following platforms:\n\n* the operating panel on the pump\n* Grundfos GO\n* Grundfos GO Link\n* the central management system.\nThe purpose of controlling an E-pump is to monitor and control the pressure, temperature, flow rate and liquid level of the system.\n\n",
#         "---\nSource title: CME, CM (Data booklet)\nBreadcrumbs: The pump uses the input from the sensor to control the differential temperature.\n  / Constant flow rate / Constant flow rate / Control of E-pumps\n---\n\n##### Control options\n\nIt is possible to communicate with E-pumps via the following platforms:\n\n* the operating panel on the pump\n* Grundfos GO\n* Grundfos GO Link\n* the central management system.\nThe purpose of controlling an E-pump is to monitor and control the pressure, temperature, flow rate and liquid level of the system.\n\n",
#     ]
#     main(questions, documents)
