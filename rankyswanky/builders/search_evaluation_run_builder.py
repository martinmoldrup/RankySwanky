from rankyswanky.models.retrieval_evaluation_models import QueryResults, SearchEvaluationRun, TestConfiguration, AggregatedRetrievalMetrics

class SearchEvaluationRunBuilder:
    """Builder for SearchEvaluationRun objects."""

    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self.reset()

    def reset(self) -> 'SearchEvaluationRunBuilder':
        """Reset the builder to its initial state."""
        self._test_configuration = None  # type: TestConfiguration | None
        self._query_results: list[QueryResults] = []
        self._retrieval_metrics = None  # type: AggregatedRetrievalMetrics | None
        self._engine_name: str | None = None
        return self

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
