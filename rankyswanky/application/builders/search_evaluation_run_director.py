import time
import logging
from collections.abc import Callable
from rankyswanky.application.builders.query_results_builder import QueryResultsBuilder
from rankyswanky.application.builders.search_evaluation_run_builder import (
    SearchEvaluationRunBuilder,
)
from rankyswanky.application.metrics.aggregated_metrics import calculate_aggregated_retrieval_metrics
from rankyswanky.application.metrics.retrieved_document_metrics import RelevanceEvaluator, RelevanceEvaluatorBase
from rankyswanky.models.retrieval_evaluation_models import (
    QueryResults,
    RetrievedDocumentMetrics,
    SearchEvaluationRun,
    TestConfiguration,
)

logger = logging.getLogger(__name__)


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
        """The main object we are building for a bulk evaluation run, we build a single of these per run."""

        self._query_results_builder = query_results_builder
        """Builder for the inner QueryResults objects we build multiple of these, one per query."""

        self._relevance_evaluator = relevance_evaluator
        """Class to be used calculate the relevance added to the QueryResults objects."""

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
        for i, query in enumerate(queries):
            logger.info(f"Evaluating query {i + 1}/{len(queries)}: {query}")
            start_time: float = time.time()
            results: list[str] = retriever(query)
            elapsed_ms: int = round(
                (time.time() - start_time) * 1000,
            )  # Convert to milliseconds

            query_result = self._build_query_result_object(query, results, elapsed_ms)
            query_results.append(query_result)

        aggregated_metrics = calculate_aggregated_retrieval_metrics(query_results)
        return (
            self._builder.set_test_configuration(test_configuration)
            .set_query_results(query_results)
            .set_engine_name(engine_name)
            .set_retrieval_metrics(aggregated_metrics)
            .build()
        )

    def _build_query_result_object(
        self,
        query: str,
        results: list[str],
        elapsed_ms: int,
    ) -> QueryResults:
        """Build a QueryResults object for a given query and its results."""
        self._query_results_builder.reset()
        self._query_results_builder.set_ranked_search_results(results)
        self._query_results_builder.set_query(query)
        self._query_results_builder.set_retrieval_time_ms(elapsed_ms)

        self._relevance_evaluator.set_question(query)
        metrics: list[RetrievedDocumentMetrics] = []
        for search_result_content in results:
            retrieved_document_metrics = self._relevance_evaluator.create_retrieved_document_metrics(
                document_content=search_result_content,
            )
            if retrieved_document_metrics is not None:
                metrics.append(retrieved_document_metrics)
        self._query_results_builder.set_metrics(metrics)
        query_result = self._query_results_builder.build()
        return query_result


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
        test_config,
        queries,
        mock_retriever,
        "MyRetrievalEngine",
    )
    print(evaluation_run)
