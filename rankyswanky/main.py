"""Defines the main entry point and function/class signatures for RankySwanky evaluation."""
import asyncio
from typing import Callable, List, Any, Dict
from rankyswanky.retrieval_evaluation_models import RetrievedDocumentsForQuery, SearchEvaluationRun, SearchEvaluationRunCollection, TestConfiguration
from rankyswanky.retrieved_documents_for_query_builder import RetrievedDocumentsForQueryBuilder, RetrievedDocumentsForQueryDirector
from rankyswanky.search_evaluation_run_builder import SearchEvaluationRunBuilder, SearchEvaluationRunDirector




class RankySwanky:
    """Wraps search engines or retrievers and provides evaluation methods."""

    def __init__(self, retriever: Callable[[str], List[str]] | None = None) -> None:
        """Initializes RankySwanky with optional single retriever."""
        search_evaluation_builder = SearchEvaluationRunBuilder()
        self.search_evaluation_director = SearchEvaluationRunDirector(search_evaluation_builder)
        self.engines: Dict[str, Callable[[str], List[str]]] = {}
        if retriever is not None:
            self.engines["default"] = retriever

    def add_retriever(self, name: str, retriever: Callable[[str], List[str]]) -> None:
        """Adds a single named retriever to the RankySwanky instance."""
        self.engines[name] = retriever

    def add_retrievers(self, retrievers: Dict[str, Callable[[str], List[str]]]) -> None:
        """Adds multiple named retrievers to the RankySwanky instance."""
        self.engines.update(retrievers)

    def _evaluate_single_retriever(
        self, retriever: Callable[[str], List[str]], queries: List[str], test_configuration: TestConfiguration | None = None,
    ) -> SearchEvaluationRun:
        """Evaluates a single retriever on the provided queries."""
        if test_configuration is None:
            test_configuration = TestConfiguration()
        search_evaluation_run = self.search_evaluation_director.construct(
            queries= queries,
            retriever=retriever,
            test_configuration=test_configuration,
        )
        return search_evaluation_run

    def evaluate(self, queries: List[str], test_configuration: TestConfiguration | None = None) -> SearchEvaluationRunCollection:
        """Evaluates all retrievers on the provided queries and returns a SearchEvaluationRunCollection."""
        return asyncio.run(self.aevaluate(queries, test_configuration))

    async def aevaluate(self, queries: List[str], test_configuration: TestConfiguration | None = None) -> SearchEvaluationRunCollection:
        """Async: Evaluate all engines on all queries and return a SearchEvaluationRunCollection."""
        tasks = [
            asyncio.to_thread(self._evaluate_single_retriever, retriever, queries, test_configuration)
            for retriever in self.engines.values()
        ]
        results = await asyncio.gather(*tasks)
        return SearchEvaluationRunCollection(runs=list(results))

    @classmethod
    def quick_compare(
        cls,
        retrievers: Dict[str, Callable[[str], List[str]]],
        queries: List[str],
        test_configuration: TestConfiguration | None = None,
    ) -> SearchEvaluationRunCollection:
        """Quickly compares multiple retrievers without explicit setup, returning a SearchEvaluationRunCollection."""
        instance = cls()
        instance.add_retrievers(retrievers)
        return instance.evaluate(queries, test_configuration)


if __name__ == "__main__":
    query = "What is the capital of France?"
    def my_search_engine(query: str) -> list[str]:
        """Dummy search engine that returns a fixed response."""
        search_results = [
            "France's capital is Paris.",
            "Paris is known for its art, fashion, and culture.",
            "There is a dish called 'French fries' that is popular in many countries.",
        ]
        return search_results

    ranky = RankySwanky(retriever=my_search_engine)
    results = ranky.evaluate([query])
    results.print_summary()