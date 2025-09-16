from abc import ABC, abstractmethod
from rankyswanky.models.retrieval_evaluation_models import RetrievedDocumentMetrics


class RelevanceEvaluatorBase(ABC):
    @abstractmethod
    def set_question(self, question: str) -> None:
        """Set the question for the relevance evaluator."""
        pass

    @abstractmethod
    def create_retrieved_document_metrics(self, context: str) -> RetrievedDocumentMetrics | None:
        """Get the relevance score of the context to the question using an LLM."""
        pass

    