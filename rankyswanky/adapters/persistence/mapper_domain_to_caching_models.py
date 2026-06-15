"""
Mapper between domain models and caching (persistence) models.

This module contains pure mapping functions to translate between
domain-layer models (used during evaluation and ranking) and
infrastructure-layer models (SQLModel entities used for caching/persistence).

The mappers avoid side-effects and I/O, making them easy to unit test
and reuse across adapters. ID/hash strategies are deterministic by default
to keep the mapping stable, but can be overridden by passing callables.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
from rankyswanky.adapters.persistence.caching_models import (
    Document as PersistedDocument,
)
from rankyswanky.adapters.persistence.caching_models import (
    DocumentRelevanceEvaluationCache as PersistedDocumentRelevanceEvaluation,
)
from rankyswanky.adapters.persistence.caching_models import (
    Query as PersistedQuery,
)
from rankyswanky.adapters.persistence.caching_models import (
    QueryEvaluationCriteriaCache as PersistedGenEvalParams,
)
from rankyswanky.adapters.persistence.caching_models import (
    UserProfile as PersistedUserProfile,
)
from rankyswanky.models.metric_calculation_models import (
    QuestionWithRewritesAndCorrectnessProps,
    RetrievedDocumentStatistics,
)
from rankyswanky.models.retrieval_evaluation_models import QueryResults, RetrievedDocument
from typing import Protocol, runtime_checkable

# -----------------------------
# ID/Hash strategies
# -----------------------------


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def default_document_id_strategy(content: str) -> str:
    """Create a stable document ID from content using SHA-256 hex digest."""
    return sha256(content.encode("utf-8")).hexdigest()


def default_query_id_strategy(text: str) -> str:
    """Create a stable query ID from text using SHA-256 hex digest."""
    return sha256(text.encode("utf-8")).hexdigest()


def default_document_hash_strategy(content: str, embedding_vector: list[float] | None = None) -> str:
    """Create a stable hash for a document combining content and optional embedding vector."""
    m = sha256()
    m.update(content.encode("utf-8"))
    if embedding_vector:
        # Include a bounded precision representation to keep hash deterministic
        vector_str = ",".join(f"{v:.8f}" for v in embedding_vector)
        m.update(vector_str.encode("utf-8"))
    return m.hexdigest()


def default_perspective_id_strategy(perspective_text: str) -> str:
    """Create a stable perspective ID from the perspective text using SHA-256 hex digest."""
    return sha256(perspective_text.encode("utf-8")).hexdigest()


def default_query_evaluation_criterias_id_strategy(query_id: str, perspective_id: str) -> str:
    """Create a stable primary key for QueryEvaluationCriteriaCache from query+perspective IDs."""
    return sha256(f"{query_id}:{perspective_id}".encode()).hexdigest()


def default_document_statistics_strategy(query_id: str, perspective_id: str, document_id: str) -> str:
    """Create a stable document ID from content using SHA-256 hex digest."""
    return sha256(f"{query_id}:{perspective_id}:{document_id}".encode()).hexdigest()


# -----------------------------
# Domain -> Persistence mapping
# -----------------------------


def map_retrieved_document_to_persisted_document(
    rd: RetrievedDocument,
    *,
    id_strategy: Callable[[str], str] = default_document_id_strategy,
    hash_strategy: Callable[[str, list[float] | None], str] = default_document_hash_strategy,
    timestamp_factory: Callable[[], datetime] = _utcnow,
) -> PersistedDocument:
    """Map a domain RetrievedDocument to a persistable Document."""
    content: str = rd.document_content
    embedding: list[float] = rd.embedding_vector or []
    doc_id: str = id_strategy(content)
    doc_hash: str = hash_strategy(content, embedding)
    return PersistedDocument(
        id=doc_id,
        content=content,
        embedding_vector=embedding,
        hash=doc_hash,
        timestamp=timestamp_factory(),
    )


def map_query_results_to_persisted_query(
    qr: QueryResults,
    *,
    id_strategy: Callable[[str], str] = default_query_id_strategy,
    timestamp_factory: Callable[[], datetime] = _utcnow,
) -> PersistedQuery:
    """Map a domain QueryResults to a persistable Query entity."""
    qid: str = id_strategy(qr.query)
    return PersistedQuery(
        id=qid,
        text=qr.query,
        embedding_vector=[],  # embedding may be unknown at this layer
        timestamp=timestamp_factory(),
    )


def map_perspective_to_persisted_user_profile(
    perspective: str,
    *,
    description: str = "",
    id_strategy: Callable[[str], str] = default_perspective_id_strategy,
    timestamp_factory: Callable[[], datetime] = _utcnow,
) -> PersistedUserProfile:
    """Map a perspective string to a persistable UserProfile entity."""
    return PersistedUserProfile(
        id=id_strategy(perspective),
        name=perspective,
        description=description or perspective,
        timestamp=timestamp_factory(),
    )


def map_retrieved_document_statistics_to_document_relevance_evaluation(
    *,
    question: str,
    perspective: str,
    document_content: str,
    params: RetrievedDocumentStatistics,
    timestamp_factory: Callable[[], datetime] = _utcnow,
) -> PersistedDocumentRelevanceEvaluation:
    """Map retrieved document statistics to DocumentRelevanceEvaluationCache."""
    query_id = default_query_id_strategy(question)
    perspective_id = default_perspective_id_strategy(perspective)
    document_id = default_document_id_strategy(document_content)
    row_id = default_document_statistics_strategy(query_id, perspective_id, document_id)
    return PersistedDocumentRelevanceEvaluation(
        id=row_id,
        document_id=document_id,
        user_profile_id=perspective_id,
        query_id=query_id,
        relevance_score=params.relevance,
        query_evaluation_criteria_id=default_query_evaluation_criterias_id_strategy(query_id, perspective_id),
        criteria_met=dict(params.evaluated_properties_of_a_good_document),
        timestamp=timestamp_factory(),
    )


# -----------------------------
# Persistence -> Domain mapping
# -----------------------------


def map_persisted_document_relevance_evaluation_to_retrieved_document_statistics(
    persisted: PersistedDocumentRelevanceEvaluation,
) -> RetrievedDocumentStatistics:
    """Map DocumentRelevanceEvaluationCache to domain RetrievedDocumentStatistics."""
    return RetrievedDocumentStatistics(
        relevance=persisted.relevance_score,
        evaluated_properties_of_a_good_document=dict(persisted.criteria_met),
    )


# -----------------------------
# Gen/Eval question parameters mapping
# -----------------------------


@runtime_checkable
class CombinedOutputLike(Protocol):
    """Protocol for compatibility with CombinedOutput model in utils module."""

    question: str
    perspective: str
    rewritten_questions: list[str]
    properties_of_a_good_document_containing_all_perspectives: list[str]


def map_combined_output_to_gen_and_evaluate_params(
    combined: CombinedOutputLike,
    *,
    query_id_strategy: Callable[[str], str] = default_query_id_strategy,
    perspective_id_strategy: Callable[[str], str] = default_perspective_id_strategy,
    gen_eval_id_strategy: Callable[[str, str], str] = default_query_evaluation_criterias_id_strategy,
) -> PersistedGenEvalParams:
    """
    Map a CombinedOutput-like object to QueryEvaluationCriteriaCache.

    - query_id is derived from the original question text to align with persisted Query IDs.
    - perspective_id is derived from the perspective text (caller may override strategy).
    - primary key is a stable hash of (query_id, perspective_id) to allow idempotent upserts.
    """
    query_id = query_id_strategy(combined.question)
    perspective_id = perspective_id_strategy(combined.perspective)
    row_id = gen_eval_id_strategy(query_id, perspective_id)
    return PersistedGenEvalParams(
        id=row_id,
        query_id=query_id,
        user_profile_id=perspective_id,
        query_rewrites=list(combined.rewritten_questions),
        evaluation_criteria=list(
            combined.properties_of_a_good_document_containing_all_perspectives,
        ),
    )


def map_question_with_rewrites_and_correctness_props_to_gen_and_evaluate_params(
    params: QuestionWithRewritesAndCorrectnessProps,
    *,
    query_id_strategy: Callable[[str], str] = default_query_id_strategy,
    perspective_id_strategy: Callable[[str], str] = default_perspective_id_strategy,
    gen_eval_id_strategy: Callable[[str, str], str] = default_query_evaluation_criterias_id_strategy,
) -> PersistedGenEvalParams:
    """Map domain question rewrite+criteria params to QueryEvaluationCriteriaCache."""
    query_id = query_id_strategy(params.question)
    perspective_id = perspective_id_strategy(params.perspective)
    row_id = gen_eval_id_strategy(query_id, perspective_id)
    return PersistedGenEvalParams(
        id=row_id,
        query_id=query_id,
        user_profile_id=perspective_id,
        query_rewrites=list(params.rewritten_questions),
        evaluation_criteria=list(params.properties_of_a_good_document_containing_all_perspectives),
    )


def map_gen_and_evaluate_params_to_question_with_rewrites_and_correctness_props(
    persisted: PersistedGenEvalParams,
    *,
    question: str,
    perspective: str,
) -> QuestionWithRewritesAndCorrectnessProps:
    """Map QueryEvaluationCriteriaCache to domain question rewrite+criteria params."""
    return QuestionWithRewritesAndCorrectnessProps(
        rewritten_questions=list(persisted.query_rewrites),
        question=question,
        perspective=perspective,
        properties_of_a_good_document_containing_all_perspectives=list(persisted.evaluation_criteria),
    )
