from typing import Callable
from rankyswanky.retrieved_documents_for_query_builder import RetrievedDocumentsForQueryBuilder, RetrievedDocumentsForQueryDirector
from rankyswanky.retrieval_evaluation_models import QueryResults, SearchEvaluationRun, TestConfiguration, AggregatedRetrievalMetrics
import time

class SearchEvaluationRunBuilder:
    """Builder for SearchEvaluationRun objects."""

    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self._test_configuration = None  # type: Optional[TestConfiguration]
        self._query_results: list[QueryResults] = []
        self._retrieval_metrics = None  # type: Optional[AggregatedRetrievalMetrics]
        self._engine_name: str | None = None

    def set_test_configuration(self, test_configuration: TestConfiguration) -> 'SearchEvaluationRunBuilder':
        """Set the test configuration for the evaluation run."""
        self._test_configuration = test_configuration
        return self

    def add_query_result(self, query_result: QueryResults) -> 'SearchEvaluationRunBuilder':
        """Add a QueryResults to the evaluation run."""
        self._query_results.append(query_result)
        return self

    def set_query_results(self, query_results: list[QueryResults]) -> 'SearchEvaluationRunBuilder':
        """Set the list of QueryResultss for the evaluation run."""
        self._query_results = query_results
        return self

    def set_retrieval_metrics(self, retrieval_metrics: 'AggregatedRetrievalMetrics') -> 'SearchEvaluationRunBuilder':
        """Set the retrieval metrics for the evaluation run."""
        self._retrieval_metrics = retrieval_metrics
        return self
    
    def set_engine_name(self, engine_name: str) -> 'SearchEvaluationRunBuilder':
        self._engine_name = engine_name
        return self

    def build(self) -> SearchEvaluationRun:
        """Build and return the SearchEvaluationRun object."""
        if self._test_configuration is None:
            raise ValueError("Test configuration must be set.")
        if self._engine_name is None:
            raise ValueError("Engine name must be set.")
        return SearchEvaluationRun(
            test_configuration=self._test_configuration,
            per_query_results=self._query_results,
            overall_retrieval_metrics=self._retrieval_metrics,
            engine_name=self._engine_name,
        )
    
class SearchEvaluationRunDirector:
    """Director for building SearchEvaluationRun objects using the builder pattern."""
    _builder: SearchEvaluationRunBuilder
    def __init__(self, builder: SearchEvaluationRunBuilder) -> None:
        """Initialize the director with a builder."""
        self._builder = builder
        query_result_builder = RetrievedDocumentsForQueryBuilder()
        self._query_result_director = RetrievedDocumentsForQueryDirector(query_result_builder)

    def construct(self, test_configuration: TestConfiguration, queries: list[str], retriever: Callable[[str], list[str]], engine_name: str) -> SearchEvaluationRun:
        """Construct a SearchEvaluationRun using the provided parameters."""
        query_results = []
        for query in queries:
            start_time: float = time.time()
            results: list[str] = retriever(query)
            elapsed_ms: int = round((time.time() - start_time) * 1000)  # Convert to milliseconds
            query_results.append(self._query_result_director.construct(query, results, elapsed_ms))
        return self._builder.set_test_configuration(test_configuration).set_query_results(query_results).set_engine_name(engine_name).build()
    
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

    evaluation_run = director.construct(test_config, queries, mock_retriever, "MyRetrievalEngine")
    print(evaluation_run)