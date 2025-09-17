from typing import Optional
from rankyswanky.models.repositories import QuestionWithRewritesAndCorrectnessPropsRepository
from rankyswanky.models.metric_calculation_models import QuestionWithRewritesAndCorrectnessProps

from rankyswanky.adapters.persistence import mapper_domain_to_caching_models, pydantic_caching
from rankyswanky.adapters.persistence.caching_models import GenAndEvaluateQuestionParameters
from experimentation.calc_gain_gen_and_eval_question_parameters.grundfos_perspective import Perspective, perspectives


class QuestionWithRewritesAndCorrectnessPropsRepositorySQLite(QuestionWithRewritesAndCorrectnessPropsRepository):
    """SQLite implementation of QuestionWithRewritesAndCorrectnessPropsRepository."""

    def get_by_question_and_perspective(self, question: str, perspective: str) -> Optional[QuestionWithRewritesAndCorrectnessProps]:
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=GenAndEvaluateQuestionParameters,
            primary_key_value=mapper_domain_to_caching_models.default_gen_eval_id_strategy(query_id=mapper_domain_to_caching_models.default_query_id_strategy(question),perspective_id=mapper_domain_to_caching_models.default_perspective_id_strategy(perspectives[0].to_repr_relevant_to_rewrite()))
        )
        if not persisted_model:
            return None
        return QuestionWithRewritesAndCorrectnessProps(
            question=question,
            perspective="",
            rewritten_questions=persisted_model.rewritten_questions,
            properties_of_a_good_document_containing_all_perspectives=persisted_model.properties_of_a_good_document_containing_all_perspectives,
        )

    def save(self, params: QuestionWithRewritesAndCorrectnessProps) -> None:
        persistence_obj = mapper_domain_to_caching_models.map_combined_output_to_gen_and_evaluate_params(params)
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])

