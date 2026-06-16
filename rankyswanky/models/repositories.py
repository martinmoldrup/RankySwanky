"""Abstract repository interfaces for persistence / caching models."""
from abc import ABC, abstractmethod
from rankyswanky.models.metric_calculation_models import (
    QuestionWithRewritesAndCorrectnessProps,
    RetrievedDocumentStatistics,
)


class QuestionWithRewritesAndCorrectnessPropsRepository(ABC):
    """Repository for QuestionWithRewritesAndCorrectnessProps persistence."""

    @abstractmethod
    def get_by_question_and_perspective(self, question: str, perspective: str) -> QuestionWithRewritesAndCorrectnessProps | None:
        # ...use your mapping and pydantic_caching logic here...
        pass

    @abstractmethod
    def save(self, params: QuestionWithRewritesAndCorrectnessProps) -> None:
        # ...save logic...
        pass


class DocumentRepository(ABC):
    """Repository for Document persistence."""

    @abstractmethod
    def get_by_question_and_perspective_and_document(self, question: str, perspective: str, document_content: str) -> RetrievedDocumentStatistics | None:
        """Retrieve a document by its ID."""

    @abstractmethod
    def save(self, question: str, perspective: str, document_content: str, params: RetrievedDocumentStatistics) -> None:
        """Save a document with its ID and content."""


class QueryRepository(ABC):
    """Repository for Query persistence."""

    @abstractmethod
    def get_by_text(self, query_text: str) -> str | None:
        """Retrieve a query by its text, returning the query ID if cached."""

    @abstractmethod
    def save(self, query_text: str) -> str:
        """Save a query and return its generated ID."""


class UserProfileRepository(ABC):
    """Repository for UserProfile persistence."""

    @abstractmethod
    def get_by_name(self, name: str) -> str | None:
        """Retrieve a user profile ID by its name."""

    @abstractmethod
    def save(self, name: str, description: str = "") -> str:
        """Save a user profile and return its generated ID."""


class CachingStrategy(ABC):
    """Bundles the cache repositories required by evaluation components."""

    @property
    @abstractmethod
    def question_criteria_repo(self) -> QuestionWithRewritesAndCorrectnessPropsRepository:
        """Return repository for question criteria caching."""

    @property
    @abstractmethod
    def document_repo(self) -> DocumentRepository:
        """Return repository for document evaluation caching."""

    @property
    @abstractmethod
    def query_repo(self) -> QueryRepository:
        """Return repository for query caching."""

    @property
    @abstractmethod
    def user_profile_repo(self) -> UserProfileRepository:
        """Return repository for user profile caching."""
