from typing import Any
from rankyswanky.retrieval_evaluation_models import RetrievedDocumentsForQuery, RetrievedDocument, RetrievedDocumentMetrics
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
        self.embeddings: list[float] | None = None
        self.metrics: list[RetrievedDocumentMetrics] | None = None

    def set_query(self, query: str) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the query for the search results."""
        self.query = query
        return self

    def set_ranked_search_results(self, ranked_search_results: list[str]) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the search results and the rank."""
        self.ranked_search_results = ranked_search_results
        return self
    
    def set_answer(self, answer: str) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the answer for the query."""
        self.answer = answer
        return self
    
    def set_embeddings(self, embeddings: list[float]) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the vector embeddings for the search results."""
        self.embeddings = embeddings
        return self
    
    def set_metrics(self, metrics: list[RetrievedDocumentMetrics]) -> "RetrievedDocumentsForQueryBuilder":
        """Sets the metrics for the search results."""
        self.metrics = metrics
        return self

    def build(self) -> RetrievedDocumentsForQuery:
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
                retrieved_document_metrics=self.metrics[i] if self.metrics else None
            )
            for i, content in enumerate(self.ranked_search_results)
        ]

        return RetrievedDocumentsForQuery(
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
        )

    def construct(self, query: str, search_results: list[Any]) -> RetrievedDocumentsForQuery:
        """Constructs a RetrievedDocumentsForQuery using the builder."""
        self.builder.set_ranked_search_results(search_results)
        self.builder.set_query(query)

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
    
    query_result = director.construct(query, search_results)
    print(query_result.model_dump())