from typing import Callable
from rankyswanky.builders.query_results_builder import QueryResultsBuilder
from rankyswanky.builders.search_evaluation_run_builder import (
    SearchEvaluationRunBuilder,
)
from rankyswanky.models.retrieval_evaluation_models import (
    QueryResults,
    RetrievedDocumentMetrics,
    SearchEvaluationRun,
    TestConfiguration,
)
from rankyswanky.utils.retrieved_document_metrics import RelevanceEvaluatorBase, RelevanceEvaluator
from rankyswanky.utils.aggregated_metrics import calculate_aggregated_retrieval_metrics
import time


class SearchEvaluationRunDirector:
    """Director for building SearchEvaluationRun objects using the builder pattern."""

    _builder: SearchEvaluationRunBuilder

    def __init__(
        self,
        evaluation_run_builder: SearchEvaluationRunBuilder,
        query_results_builder: QueryResultsBuilder,
        relevance_evaluator: RelevanceEvaluatorBase,
    ) -> None:
        """Initialize the director with a builder."""
        self._builder = evaluation_run_builder
        self._query_results_builder = query_results_builder
        self._relevance_evaluator = relevance_evaluator

    def construct(
        self,
        test_configuration: TestConfiguration,
        queries: list[str],
        retriever: Callable[[str], list[str]],
        engine_name: str,
    ) -> SearchEvaluationRun:
        """Construct a SearchEvaluationRun using the provided parameters."""
        self._builder.reset()
        query_results: list[QueryResults] = []
        for query in queries:
            start_time: float = time.time()
            results: list[str] = retriever(query)
            elapsed_ms: int = round(
                (time.time() - start_time) * 1000
            )  # Convert to milliseconds

            query_result = self.build_query_result_object(query, results, elapsed_ms)
            query_results.append(query_result)

        aggregated_metrics = calculate_aggregated_retrieval_metrics(query_results)
        return (
            self._builder.set_test_configuration(test_configuration)
            .set_query_results(query_results)
            .set_engine_name(engine_name)
            .set_retrieval_metrics(aggregated_metrics)
            .build()
        )

    def build_query_result_object(
        self, query: str, results: list[str], elapsed_ms: int
    ) -> QueryResults:
        """Build a QueryResults object for a given query and its results."""
        self._query_results_builder.reset()
        self._query_results_builder.set_ranked_search_results(results)
        self._query_results_builder.set_query(query)
        self._query_results_builder.set_retrieval_time_ms(elapsed_ms)

        self._relevance_evaluator.set_question(query)
        metrics = [
            self._calculate_metrics_for_a_document(search_result_content)
            for search_result_content in results
        ]
        self._query_results_builder.set_metrics(metrics)
        query_result = self._query_results_builder.build()
        return query_result

    def _calculate_metrics_for_a_document(
        self, search_result_content: str
    ) -> RetrievedDocumentMetrics:
        """Calculate per-document metrics for a given query and result content."""
        retrieved_document_metrics = (
            self._relevance_evaluator.create_retrieved_document_metrics(
                context=search_result_content
            )
        )
        return retrieved_document_metrics


if __name__ == "__main__":
    # Example usage
    builder = SearchEvaluationRunBuilder()
    query_results_builder = QueryResultsBuilder()
    relevance_evaluator = RelevanceEvaluator()
    director = SearchEvaluationRunDirector(builder, query_results_builder, relevance_evaluator)

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

    evaluation_run = director.construct(
        test_config, queries, mock_retriever, "MyRetrievalEngine"
    )
    print(evaluation_run)
