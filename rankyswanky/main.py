"""Defines the main entry point and function/class signatures for RankySwanky evaluation."""
import asyncio
from typing import Callable, List, Any, Dict
from rankyswanky.retrieval_evaluation_models import SearchEvaluationRun, QueryResult




class SearchEvaluationRunBuilder:
    """Builder for creating SearchEvaluationRun objects."""

    def __init__(self, test_configuration: Any) -> None:
        """Initializes the builder with a test configuration."""
        self.test_configuration = test_configuration
        self.search_results: List[Any] = []
        self.retrieval_metrics: Any = None


class RankySwanky:
    """Wraps search engines or retrievers and provides evaluation methods."""

    def __init__(self, retriever: Callable[[str], List[str]] = None) -> None:
        """Initializes RankySwanky with optional single retriever."""
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
        self, retriever: Callable[[str], List[str]], queries: List[str]
    ) -> SearchEvaluationRun:
        """Evaluates a single retriever on the provided queries."""


    def evaluate(self, queries: List[str]) -> list[SearchEvaluationRun]:
        """Evaluates all retrievers on the provided queries and returns a comparison run."""
        return asyncio.run(self.aevaluate(queries))

    async def aevaluate(self, queries: List[str]) -> Any:
        """Async: Evaluate all engines on all queries."""
        # TODO

    @classmethod
    def quick_compare(
        cls,
        retrievers: Dict[str, Callable[[str], List[str]]],
        queries: List[str]
    ) -> SearchEvaluationRun:
        """Quickly compares multiple retrievers without explicit setup."""
        instance = cls()
        instance.add_retrievers(retrievers)
        return instance.evaluate(queries)
