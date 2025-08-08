"""
Calculate metrics for evaluating retrieval systems and ranking search results.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class TestConfiguration(BaseModel):
    """Test configuration."""

    embedding_model: str = "text-embedding-3-large"
    """The embedding model to use."""

    distance_function: str = "cosine"
    """The distance function to use."""


class RetrievalMetricsAtK(BaseModel):
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

    - multiply relevance with the novelty, gain is only achieved for novel results

    Instead of normalizing using the INCG we use the max relevance value times k
    Alternatively have a number N (N > k) of retrieved documents, and sort the N results when calculating INCG for k
    """

class AggregatedRetrievalMetrics(BaseModel):
    """Aggregated metrics for evaluating retrieval systems."""


    mean_relevance: float
    """Relevance of the retrieved documents."""

    mean_novelty: float
    """Novelty of the retrieved documents, e.g. how much they add new information compared to previous documents."""

    mean_reciprocal_rank: float
    """Mean Reciprocal Rank (MRR) for the retrieved documents."""

    metrics_at_k: dict[int, RetrievalMetricsAtK ] = Field(default_factory=dict)


class GainCalculationMethod(Enum):
    """Configuration options for different methods for calculating gains for retrieved documents."""

    RELEVANCE_ONLY = "relevance_only"
    RELEVANCE_AND_DIVERSITY = "relevance_and_diversity"



class RetrievedDocumentMetrics(BaseModel):
    """Metrics for a single retrieved document."""

    relevance: float
    """Relevance of the retrieved document."""

    novelty: float
    """Novelty of the retrieved document, e.g. how much it adds new information compared to previous documents."""

    # average_precision_at_k: dict[int, AveragePrecisionAtK] = Field(default_factory=dict)
    # """Average Precision at specific ranks k for the retrieved document."""

    def calculate_gain(self, method: GainCalculationMethod) -> float:
        """Calculate the gain for the retrieved document."""
        if method == GainCalculationMethod.RELEVANCE_ONLY:
            return self.relevance
        else:
            raise ValueError(f"Unknown method: {method}")


class PerQueryRetrievalMetrics(AggregatedRetrievalMetrics):
    """Metrics for evaluating the retrieval of documents for a query."""  


class RetrievedDocument(BaseModel):
    """A single retrieved document with ranking and metrics."""

    document_content: str
    """The document that was retrieved."""

    rank: int
    """The rank of the retrieved document."""

    embedding_vector: list[float] = Field(default_factory=list)
    """The vector embeddings of the retrieved document."""

    retrieved_document_metrics: Optional[RetrievedDocumentMetrics] = None
    """Metrics for the retrieved document. This will be calculated in a separate step. Will be None if not calculated yet."""

    retrieval_time_ms: int
    """The time it took to retrieve the document in milliseconds."""

class QueryResults(BaseModel):
    """Results for a single query, including all retrieved documents."""

    query: str
    """The query that was used to retrieve the documents."""

    retrieved_documents: list[RetrievedDocument] = Field(default_factory=list)
    """The retrieved documents for this query."""

    query_metrics: Optional[PerQueryRetrievalMetrics] = None
    """Metrics for the query retrieval. This will be calculated in a separate step. Will be None if not calculated yet."""




class SearchEvaluationRun(BaseModel):
    """Aggregate root for a single evaluation run for the retrieval system, including all queries and aggregated metrics."""

    engine_name: str
    """The name of the retrieval engine being evaluated."""

    test_configuration: TestConfiguration
    """The test configuration."""

    per_query_results: list[QueryResults] = Field(default_factory=list)
    """The results for each query in this evaluation run."""

    overall_retrieval_metrics: Optional[AggregatedRetrievalMetrics] = None
    """The aggregated metrics for the retrieval system."""

    def summary(self) -> Panel:
        """Create a rich-formatted string summarizing the evaluation run."""

        table: Table = Table(title=f"Search Evaluation Run Summary for {self.engine_name}")

        table.add_column("Test Configuration", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row("Embedding Model", self.test_configuration.embedding_model)
        table.add_row("Distance Function", self.test_configuration.distance_function)
        table.add_row("Number of Queries", str(len(self.per_query_results)))

        # if self.overall_retrieval_metrics:
        #     table.add_row("NDCG", f"{self.overall_retrieval_metrics.normalized_discounted_cumulative_gain:.4f}")
        #     table.add_row("NCG", f"{self.overall_retrieval_metrics.normalized_cumulative_gain:.4f}")
        #     table.add_row("Mean Relevance", f"{self.overall_retrieval_metrics.mean_relevance:.4f}")
        # else:
        #     table.add_row("Overall Retrieval Metrics", "Not calculated yet.")

        panel: Panel = Panel(table, title="Evaluation Run", expand=False)
        return panel

    def print_summary(self) -> None:
        """Print the summary of the evaluation run in rich format."""
        console: Console = Console()
        console.print(self.summary())

class SearchEvaluationRunCollection(BaseModel):
    """Aggregate root for a collection of SearchEvaluationRun objects, used for comparison and analysis."""

    runs: list[SearchEvaluationRun] = Field(default_factory=list)
    """List of SearchEvaluationRun instances."""

    def print_summary(self) -> None:
        """Print the summary of all runs in rich format."""
        console: Console = Console()
        for run in self.runs:
            console.print(run.summary())

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
