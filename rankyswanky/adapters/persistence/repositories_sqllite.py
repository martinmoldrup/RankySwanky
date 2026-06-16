"""SQLite-based repository implementations for caching persistent data."""

from rankyswanky.adapters.persistence import (
    cache_id_strategies,
    pydantic_caching,
)
from rankyswanky.adapters.persistence.caching_models import (
    Document as PersistedDocument,
)
from rankyswanky.adapters.persistence.caching_models import (
    DocumentRelevanceEvaluationCache,
    QueryEvaluationCriteriaCache,
)
from rankyswanky.adapters.persistence.caching_models import (
    Query as PersistedQuery,
)
from rankyswanky.adapters.persistence.caching_models import (
    UserProfile as PersistedUserProfile,
)
from rankyswanky.models.metric_calculation_models import (
    QuestionWithRewritesAndCorrectnessProps,
    RetrievedDocumentStatistics,
)
from rankyswanky.models.repositories import (
    CachingStrategy,
    DocumentRepository,
    QueryRepository,
    QuestionWithRewritesAndCorrectnessPropsRepository,
    UserProfileRepository,
)


class SQLiteCachingStrategy(CachingStrategy):
    """Default SQLite-backed caching strategy for evaluation."""

    def __init__(self) -> None:
        """Initialize strategy with SQLite repository implementations."""
        self._question_criteria_repo = QuestionWithRewritesAndCorrectnessPropsRepositorySQLite()
        self._document_repo = DocumentRepositorySQLite()
        self._query_repo = QueryRepositorySQLite()
        self._user_profile_repo = UserProfileRepositorySQLite()

    @property
    def question_criteria_repo(self) -> QuestionWithRewritesAndCorrectnessPropsRepository:
        """Return repository for question criteria caching."""
        return self._question_criteria_repo

    @property
    def document_repo(self) -> DocumentRepository:
        """Return repository for document evaluation caching."""
        return self._document_repo

    @property
    def query_repo(self) -> QueryRepository:
        """Return repository for query caching."""
        return self._query_repo

    @property
    def user_profile_repo(self) -> UserProfileRepository:
        """Return repository for user profile caching."""
        return self._user_profile_repo


class QuestionWithRewritesAndCorrectnessPropsRepositorySQLite(QuestionWithRewritesAndCorrectnessPropsRepository):
    """SQLite implementation of QuestionWithRewritesAndCorrectnessPropsRepository."""

    def __init__(self) -> None:
        """Initialize repository and create database schema."""
        pydantic_caching.create_schema()
        self.query_id_strategy = cache_id_strategies.default_query_id_strategy
        self.gen_eval_id_strategy = cache_id_strategies.default_query_evaluation_criterias_id_strategy
        self.perspective_id_strategy = cache_id_strategies.default_perspective_id_strategy

    def get_by_question_and_perspective(
        self, question: str, perspective: str,
    ) -> QuestionWithRewritesAndCorrectnessProps | None:
        """Retrieve a QuestionWithRewritesAndCorrectnessProps by question and perspective."""
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=QueryEvaluationCriteriaCache,
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
            rewritten_questions=persisted_model.query_rewrites,
            properties_of_a_good_document_containing_all_perspectives=persisted_model.evaluation_criteria,
        )

    def save(self, params: QuestionWithRewritesAndCorrectnessProps) -> None:
        """Save a QuestionWithRewritesAndCorrectnessProps to the database."""
        query_id = self.query_id_strategy(params.question)
        perspective_id = self.perspective_id_strategy(params.perspective)
        row_id = self.gen_eval_id_strategy(query_id, perspective_id)
        persistence_obj = QueryEvaluationCriteriaCache(
            id=row_id,
            query_id=query_id,
            user_profile_id=perspective_id,
            query_rewrites=list(params.rewritten_questions),
            evaluation_criteria=list(
                params.properties_of_a_good_document_containing_all_perspectives,
            ),
        )
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])


class DocumentRepositorySQLite(DocumentRepository):
    """SQLite implementation of DocumentRepository."""

    def __init__(self) -> None:
        """Initialize repository with ID generation strategies and create schema."""
        pydantic_caching.create_schema()
        self.query_id_strategy = cache_id_strategies.default_query_id_strategy
        self.perspective_id_strategy = (
            cache_id_strategies.default_perspective_id_strategy
        )
        self.document_id_strategy = (
            cache_id_strategies.default_document_id_strategy
        )
        self.document_statistics_strategy = (
            cache_id_strategies.default_document_statistics_strategy
        )
        self.query_evaluation_criterias_id_strategy = (
            cache_id_strategies.default_query_evaluation_criterias_id_strategy
        )

    def get_by_question_and_perspective_and_document(
        self,
        question: str,
        perspective: str,
        document_content: str,
    ) -> RetrievedDocumentStatistics | None:
        """Retrieve document statistics by question, perspective, and document content."""
        primary_key_value = self.document_statistics_strategy(
            query_id=self.query_id_strategy(question),
            perspective_id=self.perspective_id_strategy(perspective),
            document_id=self.document_id_strategy(document_content),
        )
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=DocumentRelevanceEvaluationCache,
            primary_key_value=primary_key_value,
        )
        if not persisted_model:
            return None
        return RetrievedDocumentStatistics(
            relevance=persisted_model.relevance_score,
            evaluated_properties_of_a_good_document=persisted_model.criteria_met,
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
        document_obj = PersistedDocument(
            id=document_id,
            content=document_content,
            embedding_vector=[],
            hash=document_id,
        )
        persistence_obj = DocumentRelevanceEvaluationCache(
            id=primary_key_value,
            document_id=document_id,
            user_profile_id=perspective_id,
            query_id=query_id,
            relevance_score=params.relevance,
            query_evaluation_criteria_id=self.query_evaluation_criterias_id_strategy(query_id, perspective_id),
            criteria_met=params.evaluated_properties_of_a_good_document,
        )
        pydantic_caching.save_sqlmodels_to_db(
            [document_obj, persistence_obj],
        )


class QueryRepositorySQLite(QueryRepository):
    """SQLite implementation of QueryRepository for caching queries."""

    def __init__(self) -> None:
        """Initialize repository and create database schema."""
        pydantic_caching.create_schema()
        self.query_id_strategy = cache_id_strategies.default_query_id_strategy

    def get_by_text(self, query_text: str) -> str | None:
        """Retrieve a query ID by its text if it exists in cache."""
        query_id = self.query_id_strategy(query_text)
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=PersistedQuery,
            primary_key_value=query_id,
        )
        if not persisted_model:
            return None
        return query_id

    def save(self, query_text: str) -> str:
        """Save a query and return its ID."""
        query_id = self.query_id_strategy(query_text)
        persistence_obj = PersistedQuery(
            id=query_id,
            text=query_text,
            embedding_vector=[],
        )
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])
        return query_id


class UserProfileRepositorySQLite(UserProfileRepository):
    """SQLite implementation of UserProfileRepository for caching user perspectives."""

    def __init__(self) -> None:
        """Initialize repository and create database schema."""
        pydantic_caching.create_schema()
        self.perspective_id_strategy = cache_id_strategies.default_perspective_id_strategy

    def get_by_name(self, name: str) -> str | None:
        """Retrieve a user profile ID by its name if it exists in cache."""
        profile_id = self.perspective_id_strategy(name)
        persisted_model = pydantic_caching.get_sqlmodel_by_primary_key(
            model=PersistedUserProfile,
            primary_key_value=profile_id,
        )
        if not persisted_model:
            return None
        return profile_id

    def save(self, name: str, description: str = "") -> str:
        """Save a user profile and return its ID."""
        profile_id = self.perspective_id_strategy(name)
        persistence_obj = PersistedUserProfile(
            id=profile_id,
            name=name,
            description=description or name,
        )
        pydantic_caching.save_sqlmodels_to_db([persistence_obj])
        return profile_id
