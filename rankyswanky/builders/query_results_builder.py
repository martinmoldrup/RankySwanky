from rankyswanky.models.retrieval_evaluation_models import QueryResults, RetrievedDocument, RetrievedDocumentMetrics
from rankyswanky.metrics.aggregated_metrics import calculate_per_query_retrieval_metrics


class QueryResultsBuilder:
    """Builder for creating RetrievedDocumentsForQuery objects."""

    def __init__(self) -> None:
        """Initializes the builder with a query."""
        self.reset()

    def reset(self) -> "QueryResultsBuilder":
        """Resets the builder to its initial state."""
        self.query: str | None = None
        self.answer: str | None = None
        # Used to build the RetrievedDocument objects
        # All have the same length
        self.ranked_search_results: list[str] = []
        self.embeddings: list[list[float]] | None = None
        self.metrics: list[RetrievedDocumentMetrics] | None = None
        self.retrieval_time_ms: int | None = None
        return self

    def set_query(self, query: str) -> "QueryResultsBuilder":
        """Sets the query for the search results."""
        self.query = query
        return self

    def set_ranked_search_results(self, ranked_search_results: list[str]) -> "QueryResultsBuilder":
        """Sets the search results and the rank."""
        if self.embeddings and len(self.embeddings) != len(ranked_search_results):
            raise ValueError("Ranked search results length must match the number of embeddings.")
        if self.metrics and len(self.metrics) != len(ranked_search_results):
            raise ValueError("Ranked search results length must match the number of metrics.")
        self.ranked_search_results = ranked_search_results
        return self
    
    def set_answer(self, answer: str) -> "QueryResultsBuilder":
        """Sets the answer for the query."""
        self.answer = answer
        return self
    
    def set_embeddings(self, embeddings: list[list[float]]) -> "QueryResultsBuilder":
        """Sets the vector embeddings for the search results."""
        if self.ranked_search_results and len(self.ranked_search_results) != len(embeddings):
            raise ValueError("Embeddings length must match the number of ranked search results.")
        if self.metrics and len(self.metrics) != len(embeddings):
            raise ValueError("Embeddings length must match the number of metrics.")
        self.embeddings = embeddings
        return self
    
    def set_metrics(self, metrics: list[RetrievedDocumentMetrics]) -> "QueryResultsBuilder":
        """Sets the metrics for the search results."""
        if self.ranked_search_results and len(self.ranked_search_results) != len(metrics):
            raise ValueError("Metrics length must match the number of ranked search results.")
        if self.embeddings and len(self.embeddings) != len(metrics):
            raise ValueError("Metrics length must match the number of embeddings.")
        self.metrics = metrics
        return self
    
    def set_retrieval_time_ms(self, retrieval_time_ms: int) -> "QueryResultsBuilder":
        """Sets the retrieval time in milliseconds for the search results."""
        self.retrieval_time_ms = retrieval_time_ms
        return self

    def build(self) -> QueryResults:
        """Builds and returns a RetrievedDocumentsForQuery object."""
        if self.query is None:
            raise ValueError("Query must be set before building the RetrievedDocumentsForQuery.")
        
        if not self.ranked_search_results:
            raise ValueError("Ranked search results must be set before building the RetrievedDocumentsForQuery.")
        
        search_results = [
            RetrievedDocument(
                document_content=content,
                rank=i + 1,
                embedding_vector=self.embeddings[i] if self.embeddings else [],
                retrieved_document_metrics=self.metrics[i] if self.metrics else None,
            )
            for i, content in enumerate(self.ranked_search_results)
        ]
        return QueryResults(
            query=self.query,
            retrieved_documents=search_results,
            retrieval_time_ms=self.retrieval_time_ms if self.retrieval_time_ms is not None else 0,
            query_metrics=calculate_per_query_retrieval_metrics(search_results) if self.metrics else None
        ) 
