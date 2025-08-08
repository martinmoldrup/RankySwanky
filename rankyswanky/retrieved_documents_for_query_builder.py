from typing import Any
from rankyswanky.retrieval_evaluation_models import QueryResults, RetrievedDocument, RetrievedDocumentMetrics
from rankyswanky.retreved_document_metrics import RelevanceEvaluator

class RetrievedDocumentsForQueryBuilder:
    """Builder for creating RetrievedDocumentsForQuery objects."""

    def __init__(self) -> None:
        """Initializes the builder with a query."""
        self.query: str | None = None
        self.answer: str | None = None
        # Used to build the RetrievedDocument objects
        # All have the same length
        self.ranked_search_results: list[str] = []
        self.embeddings: list[list[float]] | None = None
        self.metrics: list[RetrievedDocumentMetrics] | None = None
        self.retrieval_time_ms: int | None = None

    def set_query(self, query: str) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the query for the search results."""
        self.query = query
        return self

    def set_ranked_search_results(self, ranked_search_results: list[str]) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the search results and the rank."""
        if self.embeddings and len(self.embeddings) != len(ranked_search_results):
            raise ValueError("Ranked search results length must match the number of embeddings.")
        if self.metrics and len(self.metrics) != len(ranked_search_results):
            raise ValueError("Ranked search results length must match the number of metrics.")
        self.ranked_search_results = ranked_search_results
        return self
    
    def set_answer(self, answer: str) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the answer for the query."""
        self.answer = answer
        return self
    
    def set_embeddings(self, embeddings: list[list[float]]) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the vector embeddings for the search results."""
        if self.ranked_search_results and len(self.ranked_search_results) != len(embeddings):
            raise ValueError("Embeddings length must match the number of ranked search results.")
        if self.metrics and len(self.metrics) != len(embeddings):
            raise ValueError("Embeddings length must match the number of metrics.")
        self.embeddings = embeddings
        return self
    
    def set_metrics(self, metrics: list[RetrievedDocumentMetrics]) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the metrics for the search results."""
        if self.ranked_search_results and len(self.ranked_search_results) != len(metrics):
            raise ValueError("Metrics length must match the number of ranked search results.")
        if self.embeddings and len(self.embeddings) != len(metrics):
            raise ValueError("Metrics length must match the number of embeddings.")
        self.metrics = metrics
        return self
    
    def set_retrieval_time_ms(self, retrieval_time_ms: int) -> "RetrievedDocumentsForQueryBuilder":
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
                retrieval_time_ms=self.retrieval_time_ms if self.retrieval_time_ms is not None else 0,
            )
            for i, content in enumerate(self.ranked_search_results)
        ]

        return QueryResults(
            query=self.query,
            retrieved_documents=search_results
        )

def calculate_cumulative_gain(relevancy_scores: list[float]) -> float:
    """Calculate the cumulative gain."""
    return sum(relevancy_scores)


def calculate_discounted_cumulative_gain(relevancy_scores: list[float]) -> float:
    """Calculate the discounted cumulative gain."""
    return sum(relevancy / (i + 1) for i, relevancy in enumerate(relevancy_scores))


def calculate_normalized_discounted_cumulative_gain(relevancy_scores: list[float]) -> float:
    """Calculate the normalized discounted cumulative gain."""
    dcg = calculate_discounted_cumulative_gain(relevancy_scores)
    ideal_dcg = calculate_discounted_cumulative_gain(sorted(relevancy_scores, reverse=True))
    return dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def calculate_normalized_cumulative_gain(relevancy_scores: list[float]) -> float:
    """We do not care about the ordering, so we do not do the discounted version."""
    cg = calculate_cumulative_gain(relevancy_scores)
    # ideally all relevancy scores are 1.0, so the ideal cumulative gain is the number of relevant contexts
    ideal_cg = len(relevancy_scores) * 1.0
    return cg / ideal_cg


class RetrievedDocumentsForQueryDirector:
    """Director for constructing RetrievedDocumentsForQuery objects using RetrievedDocumentsForQueryBuilder."""

    def __init__(self, builder: RetrievedDocumentsForQueryBuilder) -> None:
        """Initializes the director with a query result builder."""
        self.builder = builder
        self.relevance_evaluator = RelevanceEvaluator()

    def _calculate_metrics(self, search_result_content: str, query: str) -> RetrievedDocumentMetrics:
        """Calculates and returns the metrics for the search results."""
        relevance_score = self.relevance_evaluator.get_relevance_score(
            question=query, context=search_result_content
        )
        # Convert a 1-5 score to a 0-1 scale
        normalized_relevance = (relevance_score - 1) / 4 if relevance_score is not None else 0.0
        return RetrievedDocumentMetrics(
            relevance=normalized_relevance,
            novelty=0.0,  # TODO: Placeholder for novelty, can be calculated later
        )

    def construct(self, query: str, search_results: list[Any], retrieval_time_ms: int) -> QueryResults:
        """Constructs a RetrievedDocumentsForQuery using the builder."""
        self.builder.set_ranked_search_results(search_results)
        self.builder.set_query(query)
        self.builder.set_retrieval_time_ms(retrieval_time_ms)

        metrics = [
            self._calculate_metrics(search_result_content, query)
            for i, search_result_content in enumerate(search_results, start=1)
        ]

        self.builder.set_metrics(metrics)
        return self.builder.build()
    

if __name__ == "__main__":
    # Example usage
    builder = RetrievedDocumentsForQueryBuilder()
    director = RetrievedDocumentsForQueryDirector(builder)
    
    query = "What is the capital of France?"
    search_results = [
        "France's capital is Paris.",
        "Paris is known for its art, fashion, and culture.",
        "There is a dish called 'French fries' that is popular in many countries.",
    ]

    retrieval_time_ms = 100
    query_result = director.construct(query, search_results, retrieval_time_ms)
    print(query_result.model_dump())