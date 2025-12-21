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
    def get_by_id(self, query_id: str) -> str | None:
        """Retrieve a query by its ID."""

    @abstractmethod
    def save(self, query_id: str, content: str) -> None:
        """Save a query with its ID and content."""
