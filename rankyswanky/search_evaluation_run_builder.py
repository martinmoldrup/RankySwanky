from typing import Callable
from rankyswanky.retrieved_documents_for_query_builder import RetrievedDocumentsForQueryBuilder, RetrievedDocumentsForQueryDirector
from rankyswanky.retrieval_evaluation_models import RetrievedDocumentsForQuery, SearchEvaluationRun, TestConfiguration, AggregatedRetrievalMetrics

class SearchEvaluationRunBuilder:
    """Builder for SearchEvaluationRun objects."""

    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self._test_configuration = None  # type: Optional[TestConfiguration]
        self._query_results: list[RetrievedDocumentsForQuery] = []
        self._retrieval_metrics = None  # type: Optional[AggregatedRetrievalMetrics]

    def set_test_configuration(self, test_configuration: TestConfiguration) -> 'SearchEvaluationRunBuilder':
        """Set the test configuration for the evaluation run."""
        self._test_configuration = test_configuration
        return self

    def add_query_result(self, query_result: RetrievedDocumentsForQuery) -> 'SearchEvaluationRunBuilder':
        """Add a QueryResults to the evaluation run."""
        self._query_results.append(query_result)
        return self

    def set_query_results(self, query_results: list[RetrievedDocumentsForQuery]) -> 'SearchEvaluationRunBuilder':
        """Set the list of QueryResultss for the evaluation run."""
        self._query_results = query_results
        return self

    def set_retrieval_metrics(self, retrieval_metrics: 'AggregatedRetrievalMetrics') -> 'SearchEvaluationRunBuilder':
        """Set the retrieval metrics for the evaluation run."""
        self._retrieval_metrics = retrieval_metrics
        return self

    def build(self) -> SearchEvaluationRun:
        """Build and return the SearchEvaluationRun object."""
        if self._test_configuration is None:
            raise ValueError("Test configuration must be set.")
        return SearchEvaluationRun(
            test_configuration=self._test_configuration,
            per_query_results=self._query_results,
            overall_retrieval_metrics=self._retrieval_metrics
        )
    
class SearchEvaluationRunDirector:
    """Director for building SearchEvaluationRun objects using the builder pattern."""

    def __init__(self, builder: SearchEvaluationRunBuilder) -> None:
        """Initialize the director with a builder."""
        self._builder = builder
        query_result_builder = RetrievedDocumentsForQueryBuilder()
        self._query_result_director = RetrievedDocumentsForQueryDirector(query_result_builder)

    def construct(self, test_configuration: TestConfiguration, queries: list[str], retriever: Callable[[str], list[str]] ) -> SearchEvaluationRun:
        """Construct a SearchEvaluationRun using the provided parameters."""
        query_results = []
        for query in queries:
            results = retriever(query)
            query_results.append(self._query_result_director.construct(query, results))
        return self._builder.set_test_configuration(test_configuration).set_query_results(query_results).build()
    
if __name__ == "__main__":
    # Example usage
    builder = SearchEvaluationRunBuilder()
    director = SearchEvaluationRunDirector(builder)
    
    # Assuming we have a test configuration and a retriever function
    test_config = TestConfiguration()
    queries = ["What is the capital of France?", "What is the largest mammal?"]
    
    def mock_retriever(query: str) -> list[str]:
        return [
            "The capital of France is Paris.",
            "The largest mammal is the blue whale.",
            "Paris is known for the Eiffel Tower.",
            "The blue whale can grow up to 100 feet long."
            "There is a dish called 'French fries' popular in many countries.",
        ]

    evaluation_run = director.construct(test_config, queries, mock_retriever)
    print(evaluation_run)