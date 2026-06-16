"""
Cache-aware evaluation coordinator.

This module implements the caching algorithm described in the architecture documentation:
For each evaluation run, we cache expensive operations (question dimensions, document
evaluations) while computing order-dependent values (novelty, gain) fresh each time.

The coordinator implements the builder pattern to orchestrate the evaluation process
with strategic caching to avoid recomputation while respecting the order-dependent
nature of some metrics.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from rankyswanky.models.metric_calculation_models import (
    QuestionWithRewritesAndCorrectnessProps,
    RetrievedDocumentStatistics,
)
from rankyswanky.models.repositories import (
    DocumentRepository,
    QueryRepository,
    QuestionWithRewritesAndCorrectnessPropsRepository,
    UserProfileRepository,
)


@dataclass
class CachingStatistics:
    """Statistics about cache hits and misses during evaluation."""

    question_criteria_cache_hits: int = 0
    """Number of times question evaluation criteria were retrieved from cache."""

    question_criteria_cache_misses: int = 0
    """Number of times question evaluation criteria had to be calculated."""

    document_evaluation_cache_hits: int = 0
    """Number of times document evaluations were retrieved from cache."""

    document_evaluation_cache_misses: int = 0
    """Number of times document evaluations had to be calculated."""

    query_cache_hits: int = 0
    """Number of times queries were retrieved from cache."""

    query_cache_misses: int = 0
    """Number of times queries were newly cached."""

    user_profile_cache_hits: int = 0
    """Number of times user profiles were retrieved from cache."""

    user_profile_cache_misses: int = 0
    """Number of times user profiles were newly cached."""

    @property
    def total_cache_hits(self) -> int:
        """Total number of cache hits across all entity types."""
        return (
            self.question_criteria_cache_hits
            + self.document_evaluation_cache_hits
            + self.query_cache_hits
            + self.user_profile_cache_hits
        )

    @property
    def total_cache_misses(self) -> int:
        """Total number of cache misses across all entity types."""
        return (
            self.question_criteria_cache_misses
            + self.document_evaluation_cache_misses
            + self.query_cache_misses
            + self.user_profile_cache_misses
        )

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as a percentage (0-100)."""
        total = self.total_cache_hits + self.total_cache_misses
        if total == 0:
            return 0.0
        return (self.total_cache_hits / total) * 100


class CacheAwareEvaluationCoordinator:
    """
    Orchestrates cache-aware evaluation with clean separation of concerns.

    This coordinator follows the caching algorithm:
    1. For each evaluation run:
       1. For each question:
          a. Check if dimensions are cached; if not, calculate and cache them.
          b. For each document: Check if evaluations are cached; if not, evaluate and cache them.
          c. Calculate novelty and gain scores (not cached - order dependent).
       2. Calculate final metrics using cached dimensions and evaluations.

    The coordinator delegates caching to repository implementations and delegates
    domain logic to business logic layers (e.g., metric calculators).
    """

    def __init__(
        self,
        question_criteria_repo: QuestionWithRewritesAndCorrectnessPropsRepository,
        document_repo: DocumentRepository,
        query_repo: QueryRepository,
        user_profile_repo: UserProfileRepository,
    ) -> None:
        """
        Initialize the coordinator with repository dependencies.

        Args:
            question_criteria_repo: Repository for caching question evaluation criteria.
            document_repo: Repository for caching document evaluations.
            query_repo: Repository for caching queries.
            user_profile_repo: Repository for caching user profiles.

        """
        self.question_criteria_repo = question_criteria_repo
        self.document_repo = document_repo
        self.query_repo = query_repo
        self.user_profile_repo = user_profile_repo
        self.statistics = CachingStatistics()

    def get_or_create_question_criteria(
        self,
        question: str,
        perspective: str,
        compute_fn: Callable[[str, str], QuestionWithRewritesAndCorrectnessProps],
    ) -> QuestionWithRewritesAndCorrectnessProps:
        """
        Get question evaluation criteria from cache or compute and cache them.

        This implements step 1.a of the caching algorithm:
        "Check if the dimensions have already been calculated and cached.
         If not, calculate the dimensions and cache them."

        Args:
            question: The question/query text.
            perspective: The user perspective for the question.
            compute_fn: Callable that computes criteria if not cached.
                       Should accept (question, perspective) and return
                       QuestionWithRewritesAndCorrectnessProps.

        Returns:
            The question criteria, either from cache or freshly computed.

        """
        # Try to retrieve from cache
        cached = self.question_criteria_repo.get_by_question_and_perspective(
            question=question,
            perspective=perspective,
        )
        if cached is not None:
            self.statistics.question_criteria_cache_hits += 1
            return cached

        # Cache miss: compute and store
        self.statistics.question_criteria_cache_misses += 1
        criteria = compute_fn(question, perspective)
        self.question_criteria_repo.save(criteria)
        return criteria

    def prepare_question_context(
        self,
        question: str,
        perspective: str,
        compute_criteria_fn: Callable[[str, str], QuestionWithRewritesAndCorrectnessProps],
        profile_description: str = "",
    ) -> QuestionWithRewritesAndCorrectnessProps:
        """
        Prepare cache context for a question and return evaluation criteria.

        This is the preferred high-level orchestration entrypoint for callers.
        It ensures query and user profile rows are cached before reading/writing
        question criteria, keeping cache orchestration in a single place.

        Args:
            question: The question/query text.
            perspective: The user perspective for the question.
            compute_criteria_fn: Callable used to compute criteria on cache miss.
            profile_description: Optional profile description for first-time inserts.

        Returns:
            Cached or newly computed question criteria.

        """
        self.ensure_query_cached(question)
        self.ensure_user_profile_cached(perspective, profile_description)
        return self.get_or_create_question_criteria(
            question=question,
            perspective=perspective,
            compute_fn=compute_criteria_fn,
        )

    def get_or_create_document_evaluation(
        self,
        question: str,
        perspective: str,
        document_content: str,
        compute_fn: Callable[[str, str, str], RetrievedDocumentStatistics],
    ) -> RetrievedDocumentStatistics:
        """
        Get document evaluation from cache or compute and cache it.

        This implements step 1.b of the caching algorithm:
        "For each search result, check if the dimension booleans have already
         been calculated and cached. If not, run the structured output to get
         the dimension booleans and cache them."

        Args:
            question: The question/query text.
            perspective: The user perspective for evaluation.
            document_content: The document content being evaluated.
            compute_fn: Callable that computes statistics if not cached.
                       Should accept (question, perspective, document_content)
                       and return RetrievedDocumentStatistics.

        Returns:
            The document statistics, either from cache or freshly computed.

        """
        # Try to retrieve from cache
        cached = self.document_repo.get_by_question_and_perspective_and_document(
            question=question,
            perspective=perspective,
            document_content=document_content,
        )
        if cached is not None:
            self.statistics.document_evaluation_cache_hits += 1
            return cached

        # Cache miss: compute and store
        self.statistics.document_evaluation_cache_misses += 1
        evaluation = compute_fn(question, perspective, document_content)
        self.document_repo.save(
            question=question,
            perspective=perspective,
            document_content=document_content,
            params=evaluation,
        )
        return evaluation

    def ensure_query_cached(self, query_text: str) -> str:
        """
        Ensure a query is cached and return its ID.

        This supports efficient lookup and deduplication of queries.
        Uses deterministic ID generation so the same query always gets
        the same ID for cross-evaluation consistency.

        Args:
            query_text: The query/question text.

        Returns:
            The query ID (generated deterministically from query text).

        """
        # Try to retrieve from cache
        cached_id = self.query_repo.get_by_text(query_text)
        if cached_id is not None:
            self.statistics.query_cache_hits += 1
            return cached_id

        # Cache miss: store and return ID
        self.statistics.query_cache_misses += 1
        query_id = self.query_repo.save(query_text)
        return query_id

    def ensure_user_profile_cached(self, profile_name: str, description: str = "") -> str:
        """
        Ensure a user profile is cached and return its ID.

        This supports efficient lookup and reuse of perspectives across
        multiple evaluations. IDs are generated deterministically so the
        same profile always gets the same ID.

        Args:
            profile_name: The name/identifier of the user profile/perspective.
            description: Optional description of the profile.

        Returns:
            The user profile ID (generated deterministically from name).

        """
        # Try to retrieve from cache
        cached_id = self.user_profile_repo.get_by_name(profile_name)
        if cached_id is not None:
            self.statistics.user_profile_cache_hits += 1
            return cached_id

        # Cache miss: store and return ID
        self.statistics.user_profile_cache_misses += 1
        profile_id = self.user_profile_repo.save(profile_name, description)
        return profile_id

    def get_caching_statistics(self) -> CachingStatistics:
        """
        Get statistics about cache hits and misses during evaluation.

        Returns:
            CachingStatistics object with detailed hit/miss counts.

        """
        return self.statistics

    def reset_statistics(self) -> None:
        """Reset caching statistics counters."""
        self.statistics = CachingStatistics()
