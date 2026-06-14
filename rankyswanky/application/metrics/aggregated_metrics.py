from numpy import log2
from rankyswanky.models.retrieval_evaluation_models import (
    AggregatedRetrievalMetrics,
    PerQueryRetrievalMetrics,
    QueryResults,
    RetrievalMetricsAtK,
    RetrievedDocument,
    RetrievedDocumentMetrics,
)


def calculate_ndcg(gains: list[float]) -> float:
    """Calculates the normalized discounted cumulative gain (nDCG) from a list of gains."""
    if not gains:
        return 0.0
    dcg = sum((2**gain - 1) / (log2(idx + 2)) for idx, gain in enumerate(gains))
    ideal_gains = sorted(gains, reverse=True)
    idcg = sum((2**gain - 1) / (log2(idx + 2)) for idx, gain in enumerate(ideal_gains))
    return dcg / idcg if idcg > 0 else 0.0


def calculate_normalized_cumulative_gain(gains: list[float]) -> float:
    """Calculates the normalized cumulative gain (nCG) from a list of gains."""
    if not gains:
        return 0.0
    max_value_for_gain = 1  # Gain is between 0 and 1
    icg = max_value_for_gain * len(gains)
    cg = sum(gains)

    ncg = cg / icg if icg > 0 else 0.0
    return ncg


def calculate_metrics_at_k(documents: list[RetrievedDocument], k_value: int) -> RetrievalMetricsAtK:
    """Calculates retrieval metrics at a specific rank k from the list of document metrics."""
    if k_value <= 0:
        raise ValueError("k_value must be a positive integer.")
    top_k_documents = documents[:k_value]
    gains = [doc.retrieved_document_metrics.calculate_gain() for doc in top_k_documents if doc.retrieved_document_metrics]
    if not all(doc.retrieved_document_metrics for doc in top_k_documents):
        raise ValueError("All retrieved documents in the top k must have metrics to calculate metrics at k.")
    relevant_docs_within_k = sum(1 for doc in top_k_documents if doc.retrieved_document_metrics.is_relevant)
    precision = relevant_docs_within_k / k_value
    relevant_document_count = sum(1 for doc in documents if doc.retrieved_document_metrics and doc.retrieved_document_metrics.is_relevant)
    if relevant_document_count:
        recall = relevant_docs_within_k / relevant_document_count
    else:
        recall = 0.0    
    ndcg = calculate_ndcg(gains)
    return RetrievalMetricsAtK(
        precision=precision,
        recall=recall,
        f1_score=2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0,
        mean_average_precision=relevant_docs_within_k / k_value,
        normalized_discounted_cumulative_gain=ndcg,
        normalized_cumulative_gain=calculate_normalized_cumulative_gain(gains),
    )


def calculate_mean_relevance(metrics: list[RetrievedDocumentMetrics]) -> float:
    """Calculates the mean relevance from a list of document metrics."""
    return sum(doc.relevance for doc in metrics) / len(metrics) if metrics else 0


def calculate_mean_novelty(metrics: list[RetrievedDocumentMetrics]) -> float:
    """Calculates the mean novelty from a list of document metrics."""
    return sum(doc.novelty for doc in metrics) / len(metrics) if metrics else 0


def calculate_reciprocal_rank_of_first_relevant_document(documents: list[RetrievedDocument]) -> float:
    """Calculates the reciprocal rank of the first relevant document from a list of document metrics."""
    for doc in documents:
        if doc.retrieved_document_metrics and doc.retrieved_document_metrics.is_relevant:
            return 1 / (doc.rank + 1)
    return 0


def calculate_mean_reciprocal_rank(query_results: list[QueryResults]) -> float:
    """Calculates the mean reciprocal rank from a list of document metrics."""
    return sum(doc.query_metrics.reciprocal_rank_of_first_relevant_document for doc in query_results) / len(query_results) if query_results else 0


def calculate_per_query_retrieval_metrics(documents: list[RetrievedDocument]) -> PerQueryRetrievalMetrics:
    """Calculates per-query retrieval metrics from the list of document metrics."""
    if not all(doc.retrieved_document_metrics for doc in documents):
        raise ValueError("All retrieved documents must have metrics to calculate per-query metrics.")
    return PerQueryRetrievalMetrics(
        mean_relevance=calculate_mean_relevance([doc.retrieved_document_metrics for doc in documents]),
        mean_novelty=calculate_mean_novelty([doc.retrieved_document_metrics for doc in documents]),
        reciprocal_rank_of_first_relevant_document=calculate_reciprocal_rank_of_first_relevant_document(documents),
    )


def calculate_aggregated_retrieval_metrics(query_results: list[QueryResults]) -> AggregatedRetrievalMetrics:
    """Calculates aggregated retrieval metrics from the list of per-query metrics."""
    retrieved_documents = [doc for result in query_results for doc in result.retrieved_documents]
    return AggregatedRetrievalMetrics(
        mean_relevance=calculate_mean_relevance([doc.retrieved_document_metrics for doc in retrieved_documents]),
        mean_novelty=calculate_mean_novelty([doc.retrieved_document_metrics for doc in retrieved_documents]),
        mean_reciprocal_rank=calculate_mean_reciprocal_rank(query_results),
        metrics_at_k={  # TODO: make k configurable
            10: calculate_metrics_at_k(retrieved_documents, 10),
        },
    )
