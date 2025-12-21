from rankyswanky.adapters.persistence import mapper_domain_to_caching_models, pydantic_caching
from rankyswanky.adapters.persistence.caching_models import (
    DocumentMetricEvaluatedForQuestion,
    GenAndEvaluateQuestionParameters,
)
from rankyswanky.models.metric_calculation_models import (
    QuestionWithRewritesAndCorrectnessProps,
    RetrievedDocumentStatistics,
)
from rankyswanky.models.repositories import DocumentRepository, QuestionWithRewritesAndCorrectnessPropsRepository


class QuestionWithRewritesAndCorrectnessPropsRepositorySQLite(QuestionWithRewritesAndCorrectnessPropsRepository):
    """SQLite implementation of QuestionWithRewritesAndCorrectnessPropsRepository."""

    def __init__(self) -> None:
        pydantic_caching.create_schema()
        self.query_id_strategy = mapper_domain_to_caching_models.default_query_id_strategy
        self.gen_eval_id_strategy = mapper_domain_to_caching_models.default_gen_eval_id_strategy
        self.perspective_id_strategy = mapper_domain_to_caching_models.default_perspective_id_strategy

    def get_by_question_and_perspective(
        self, question: str, perspective: str,
    ) -> QuestionWithRewritesAndCorrectnessProps | None:
        """Retrieve a QuestionWithRewritesAndCorrectnessProps by question and perspective."""
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=GenAndEvaluateQuestionParameters,
            primary_key_value=self.gen_eval_id_strategy(
                query_id=self.query_id_strategy(question),
                perspective_id=self.perspective_id_strategy(perspective),
            ),
        )
        if not persisted_model:
            return None
        return QuestionWithRewritesAndCorrectnessProps(
            question=question,
            perspective=perspective,
            rewritten_questions=persisted_model.rewritten_questions,
            properties_of_a_good_document_containing_all_perspectives=persisted_model.properties_of_a_good_document_containing_all_perspectives,
        )

    def save(self, params: QuestionWithRewritesAndCorrectnessProps) -> None:
        """Save a QuestionWithRewritesAndCorrectnessProps to the database."""
        query_id = self.query_id_strategy(params.question)
        perspective_id = self.perspective_id_strategy(params.perspective)
        row_id = self.gen_eval_id_strategy(query_id, perspective_id)
        persistence_obj = GenAndEvaluateQuestionParameters(
            id=row_id,
            query_id=query_id,
            perspective_id=perspective_id,
            rewritten_questions=list(params.rewritten_questions),
            properties_of_a_good_document_containing_all_perspectives=list(
                params.properties_of_a_good_document_containing_all_perspectives,
            ),
        )
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])


class DocumentRepositorySQLite(DocumentRepository):
    """SQLite implementation of DocumentRepository."""

    def __init__(self) -> None:
        pydantic_caching.create_schema()
        self.query_id_strategy = mapper_domain_to_caching_models.default_query_id_strategy
        self.perspective_id_strategy = mapper_domain_to_caching_models.default_perspective_id_strategy
        self.document_id_strategy = mapper_domain_to_caching_models.default_document_id_strategy
        self.document_statistics_strategy = mapper_domain_to_caching_models.default_document_statistics_strategy

    def get_by_question_and_perspective_and_document(
        self,
        question: str,
        perspective: str,
        document_content: str,
    ) -> RetrievedDocumentStatistics | None:
        """Retrieve a RetrievedDocumentStatistics by question, perspective, and document content."""
        primary_key_value = self.document_statistics_strategy(
            query_id=self.query_id_strategy(question),
            perspective_id=self.perspective_id_strategy(perspective),
            document_id=self.document_id_strategy(document_content),
        )
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=DocumentMetricEvaluatedForQuestion,
            primary_key_value=primary_key_value,
        )
        if not persisted_model:
            return None
        return RetrievedDocumentStatistics(
            relevance=persisted_model.relevance_score,
            evaluated_properties_of_a_good_document=persisted_model.evaluated_properties_of_a_good_document,
        )

    def save(self, question: str, perspective: str, document_content: str, params: RetrievedDocumentStatistics) -> None:
        """Save a RetrievedDocumentStatistics to the database."""
        query_id = self.query_id_strategy(question)
        perspective_id = self.perspective_id_strategy(perspective)
        document_id = self.document_id_strategy(document_content)
        primary_key_value = self.document_statistics_strategy(
            query_id=query_id,
            perspective_id=perspective_id,
            document_id=document_id,
        )
        persistence_obj = DocumentMetricEvaluatedForQuestion(
            id=primary_key_value,
            document_id=document_id,
            perspective_id=perspective_id,
            query_id=query_id,
            relevance_score=params.relevance,
            evaluated_properties_of_a_good_document=params.evaluated_properties_of_a_good_document,
        )
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])
