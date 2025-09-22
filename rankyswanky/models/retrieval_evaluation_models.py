"""
Calculate metrics for evaluating retrieval systems and ranking search results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

RELEVANCE_THRESHOLD = 0.5
# TODO: Go though and check which values is computed based on other values and move the logic to the domain model.
# TODO: Model distilation - simplify and remove non essential parts.
@dataclass
class TestConfiguration:
    """Test configuration."""

    embedding_model: str = "text-embedding-3-large"
    """The embedding model to use."""

    distance_function: str = "cosine"
    """The distance function to use."""


@dataclass
class RetrievalMetricsAtK:
    """Metrics for evaluating retrieval systems at a specific rank k."""

    precision: float
    """Precision at rank k."""

    recall: float
    """Recall at rank k."""

    f1_score: float
    """F1 score at rank k."""

    mean_average_precision: float
    """
    Mean Average Precision (MAP) for the retrieved documents.
    Note: In RetrievedDocumentMetrics this is actually the average precision at k.
    """

    normalized_discounted_cumulative_gain: float
    """Normalized Discounted Cumulative Gain (NDCG)."""

    normalized_cumulative_gain: float
    """Normalized Cumulative Gain (NCG) where the formula is tweaked to be suitable for RAG systems.
    This is a custom not commonly used metric.

    Instead of normalizing using the INCG we use the max relevance value times k
    Alternatively have a number N (N > k) of retrieved documents, and sort the N results when calculating INCG for k
    """

@dataclass
class AggregatedRetrievalMetrics:
    """Aggregated metrics for evaluating retrieval systems."""

    mean_relevance: float
    """Relevance of the retrieved documents."""

    mean_novelty: float
    """Novelty of the retrieved documents, e.g. how much they add new information compared to previous documents."""

    mean_reciprocal_rank: float
    """Mean Reciprocal Rank (MRR) for the retrieved documents."""

    metrics_at_k: dict[int, RetrievalMetricsAtK] = field(default_factory=dict)
    """Metrics at specific ranks k."""

    def as_dict(self) -> dict[str, float]:
        """Convert the metrics to a dictionary for easy printing, including metrics at k."""
        metrics: dict[str, float] = {
            "mean_relevance": self.mean_relevance,
            "mean_novelty": self.mean_novelty,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
        }
        # Unpack metrics_at_k into key-value pairs
        for k, metric in self.metrics_at_k.items():
            metrics[f"precision_at_{k}"] = metric.precision
            metrics[f"recall_at_{k}"] = metric.recall
            metrics[f"f1_score_at_{k}"] = metric.f1_score
            metrics[f"mean_average_precision_at_{k}"] = metric.mean_average_precision
            metrics[f"ndcg_at_{k}"] = metric.normalized_discounted_cumulative_gain
            metrics[f"ncg_at_{k}"] = metric.normalized_cumulative_gain
        return metrics

class GainCalculationMethod(Enum):
    """Configuration options for different methods for calculating gains for retrieved documents."""

    RELEVANCE_ONLY = "relevance_only"
    RELEVANCE_AND_NOVELTY = "relevance_and_novelty"

@dataclass
class RetrievedDocumentMetrics:
    """Metrics for a single retrieved document."""

    relevance: float
    """Relevance of the retrieved document."""

    novelty: float
    """
    Novelty of the retrieved document, e.g. how much it adds new information compared to previous documents.

    How big a percentage of the validation criteria the retrieved documents satisfy, 
    is satisfied for the first time, compared with higher ranked documents.
    """

    @property
    def is_relevant(self) -> bool:
        """Return True if the document is relevant."""
        return self.relevance > RELEVANCE_THRESHOLD

    # average_precision_at_k: dict[int, AveragePrecisionAtK] = Field(default_factory=dict)
    # """Average Precision at specific ranks k for the retrieved document."""

    def calculate_gain(self, method: GainCalculationMethod = GainCalculationMethod.RELEVANCE_ONLY) -> float:
        """Calculate the gain for the retrieved document."""
        if method == GainCalculationMethod.RELEVANCE_ONLY:
            return self.relevance
        elif method == GainCalculationMethod.RELEVANCE_AND_NOVELTY:
            # multiply relevance with the novelty, gain is only achieved for novel results
            return self.relevance * self.novelty
        else:
            raise ValueError(f"Unknown method: {method}")

@dataclass
class PerQueryRetrievalMetrics:
    """Metrics for evaluating the retrieval of documents for a query."""
    mean_relevance: float
    """Mean relevance of the retrieved documents."""

    mean_novelty: float  # TODO: This does not make sense to calculate mean of
    """Mean novelty of the retrieved documents."""

    reciprocal_rank_of_first_relevant_document: float
    """Reciprocal Rank (RR) of the first relevant document."""

@dataclass
class RetrievedDocument:
    """A single retrieved document with ranking and metrics."""

    document_content: str
    """The document that was retrieved."""

    rank: int
    """The rank of the retrieved document."""

    embedding_vector: list[float] = field(default_factory=list)
    """The vector embeddings of the retrieved document."""

    retrieved_document_metrics: RetrievedDocumentMetrics | None = None
    """Metrics for the retrieved document. This will be calculated in a separate step. Will be None if not calculated yet."""

@dataclass
class QueryResults:
    """Results for a single query, including all retrieved documents."""

    query: str
    """The query that was used to retrieve the documents."""

    retrieved_documents: list[RetrievedDocument] = field(default_factory=list)
    """The retrieved documents for this query."""

    query_metrics: PerQueryRetrievalMetrics | None = None
    """Metrics for the query retrieval. This will be calculated in a separate step. Will be None if not calculated yet."""

    retrieval_time_ms: int = 0
    """The time it took to retrieve the documents in milliseconds."""

@dataclass
class SearchEvaluationRun:
    """Aggregate root for a single evaluation run for the retrieval system, including all queries and aggregated metrics."""

    engine_name: str
    """The name of the retrieval engine being evaluated."""

    test_configuration: TestConfiguration
    """The test configuration."""

    per_query_results: list[QueryResults] = field(default_factory=list)
    """The results for each query in this evaluation run."""

    overall_retrieval_metrics: AggregatedRetrievalMetrics | None = None
    """The aggregated metrics for the retrieval system."""

    def get_mean_retrieval_time_ms(self) -> float:
        """Get the mean retrieval time in milliseconds for the evaluation run."""
        if not self.per_query_results:
            return 0.0
        return sum(result.retrieval_time_ms for result in self.per_query_results) / len(self.per_query_results)

    def summary(self) -> Panel:
        """Create a rich-formatted string summarizing the evaluation run."""

        table: Table = Table(title=f"Search Evaluation Run Summary for {self.engine_name}")

        table.add_column("Test Configuration", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Embedding Model", self.test_configuration.embedding_model)
        table.add_row("Distance Function", self.test_configuration.distance_function)
        table.add_row("Number of Queries", str(len(self.per_query_results)))

        table.add_row("Number of Retrieved Documents", str(len(self.get_all_retrieved_documents_content())))

        if self.overall_retrieval_metrics:
            for key, value in self.overall_retrieval_metrics.as_dict().items():
                table.add_row(key.replace("_", " ").title(), f"{value:.4f}")
        else:
            table.add_row("Overall Retrieval Metrics", "Not calculated yet.")

        table.add_row("Mean Retrieval Time (ms)", f"{self.get_mean_retrieval_time_ms():.2f}")

        panel: Panel = Panel(table, title="Evaluation Run", expand=False)
        return panel

    def print_summary(self) -> None:
        """Print the summary of the evaluation run in rich format."""
        console: Console = Console()
        console.print(self.summary())

    def get_all_retrieved_documents_content(self) -> set[str]:
        """Get all retrieved documents from all queries in the evaluation run."""
        documents: list[RetrievedDocument] = []
        for result in self.per_query_results:
            documents.extend(result.retrieved_documents)
        return {doc.document_content for doc in documents}

@dataclass
class SearchEvaluationRunCollection:
    """Aggregate root for a collection of SearchEvaluationRun objects, used for comparison and analysis."""

    runs: list[SearchEvaluationRun] = field(default_factory=list)
    """List of SearchEvaluationRun instances."""

    def get_overlapping_retrieved_documents(self) -> set[str]:
        """Get the set of overlapping retrieved documents across all runs."""
        if not self.runs:
            return set()
        document_sets = [run.get_all_retrieved_documents_content() for run in self.runs]
        overlapping_documents = set.intersection(*document_sets)
        return overlapping_documents

    def print_summary(self) -> None:
        """Print the summary of all runs in rich format."""
        console: Console = Console()
        for run in self.runs:
            console.print(run.summary())
        
        console.print(f"Number of overlapping retrieved documents across all runs: {len(self.get_overlapping_retrieved_documents())}")

    def print_comparison(self) -> None:
        """
        Do a rich text print that is comparing the runs and giving an overview.
        Consider using statistical significance testing to compare the results (paired t-test, Wilcoxon signed-rank test, etc.).
        """
        raise NotImplementedError(
            "This method is not implemented yet. It should provide a rich text print of the comparison."
        )

if __name__ == "__main__":
    import erdantic as erd
    dotfile = erd.to_dot(SearchEvaluationRun)
    erd.draw(SearchEvaluationRunCollection, out="retrieval_evaluation_models.png")
