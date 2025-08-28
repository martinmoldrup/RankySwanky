from rankyswanky.models.retrieval_evaluation_models import AggregatedRetrievalMetrics, QueryResults, RetrievalMetricsAtK, RetrievedDocument, RetrievedDocumentMetrics, PerQueryRetrievalMetrics

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
        metrics_at_k={}  # TODO: Implement metrics at k calculation
    )