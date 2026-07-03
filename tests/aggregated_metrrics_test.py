import rankyswanky.models.retrieval_evaluation_models as retrieval_evaluation_models
import rankyswanky.application.metrics.aggregated_metrics as aggregated_metrics
from rankyswanky.models.retrieval_evaluation_models import RetrievedDocument, RetrievedDocumentMetrics
from unittest import mock


@mock.patch.object(retrieval_evaluation_models, "RELEVANCE_THRESHOLD", 0.5)
class TestCalculateReciprocalRank:

    def test_all_relevant(self):
        # Test data
        documents = [
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.9, novelty=0.8), document_content="doc1", rank=0),
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.7, novelty=0.6), document_content="doc2", rank=1),
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.8, novelty=0.7), document_content="doc3", rank=2),
        ]

        # Calculate aggregated metrics
        mrr = aggregated_metrics.calculate_reciprocal_rank_of_first_relevant_document(documents)

        # Assert the mean reciprocal rank, all documents is relevant
        assert mrr == 1.0

    def test_none_relevant(self):
        # Test data
        documents = [
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.4, novelty=0.3), document_content="doc1", rank=0),
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.2, novelty=0.1), document_content="doc2", rank=1),
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.3, novelty=0.2), document_content="doc3", rank=2),
        ]

        # Calculate aggregated metrics
        mrr = aggregated_metrics.calculate_reciprocal_rank_of_first_relevant_document(documents)

        # Assert the mean reciprocal rank, no documents are relevant
        assert mrr == 0.0

    def test_some_relevant(self):
        # Test data
        documents = [
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.4, novelty=0.3), document_content="doc1", rank=0),
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.2, novelty=0.1), document_content="doc2", rank=1),
            RetrievedDocument(retrieved_document_metrics=RetrievedDocumentMetrics(relevance=0.8, novelty=0.7), document_content="doc3", rank=2),
        ]

        # Calculate aggregated metrics
        mrr = aggregated_metrics.calculate_reciprocal_rank_of_first_relevant_document(documents)

        # Assert the mean reciprocal rank, some documents are relevant
        assert mrr == 1 / 3