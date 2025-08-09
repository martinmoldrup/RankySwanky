from typing import Callable
from rankyswanky.query_results_builder import QueryResultsBuilder
from rankyswanky.retrieval_evaluation_models import QueryResults, RetrievedDocumentMetrics, SearchEvaluationRun, TestConfiguration, AggregatedRetrievalMetrics
from rankyswanky.retreved_document_metrics import RelevanceEvaluator
from rankyswanky.aggregated_metrics import calculate_aggregated_retrieval_metrics
import time

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
    
class SearchEvaluationRunDirector:
    """Director for building SearchEvaluationRun objects using the builder pattern."""
    _builder: SearchEvaluationRunBuilder
    def __init__(self, evaluation_run_builder: SearchEvaluationRunBuilder, query_results_builder: QueryResultsBuilder) -> None:
        """Initialize the director with a builder."""
        self._builder = evaluation_run_builder
        self._query_results_builder = query_results_builder
        self._relevance_evaluator = RelevanceEvaluator()

 
    def construct(self, test_configuration: TestConfiguration, queries: list[str], retriever: Callable[[str], list[str]], engine_name: str) -> SearchEvaluationRun:
        """Construct a SearchEvaluationRun using the provided parameters."""
        self._builder.reset()
        query_results: list[QueryResults] = []
        for query in queries:

            start_time: float = time.time()
            results: list[str] = retriever(query)
            elapsed_ms: int = round((time.time() - start_time) * 1000)  # Convert to milliseconds

            query_result = self.build_query_result_object(query, results, elapsed_ms)
            query_results.append(query_result)

        aggregated_metrics = calculate_aggregated_retrieval_metrics(query_results)
        return self._builder.set_test_configuration(test_configuration).set_query_results(query_results).set_engine_name(engine_name).set_retrieval_metrics(aggregated_metrics).build()

    def build_query_result_object(self, query: str, results: list[str], elapsed_ms: int) -> QueryResults:
        """Build a QueryResults object for a given query and its results."""
        self._query_results_builder.reset()
        self._query_results_builder.set_ranked_search_results(results)
        self._query_results_builder.set_query(query)
        self._query_results_builder.set_retrieval_time_ms(elapsed_ms)

        metrics = [
                self._calculate_metrics_for_a_document(search_result_content, query)
                for search_result_content in results
            ]
        self._query_results_builder.set_metrics(metrics)
        query_result = self._query_results_builder.build()
        return query_result
    
    def _calculate_metrics_for_a_document(self, search_result_content: str, query: str) -> RetrievedDocumentMetrics:
        """Calculate per-document metrics for a given query and result content."""
        relevance_score = self._relevance_evaluator.get_relevance_score(
            question=query, context=search_result_content
        )
        # Convert a 1-5 score to a 0-1 scale
        normalized_relevance = (relevance_score - 1) / 4 if relevance_score is not None else 0.0
        return RetrievedDocumentMetrics(
            relevance=normalized_relevance,
            novelty=0.0,  # Placeholder for future novelty metric
        )

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