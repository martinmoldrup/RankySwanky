"""
Deterministic ID generation strategies for cache operations.

This module provides ID generation functions for converting domain entities
(queries, documents, user profiles) into stable, content-addressed cache keys.

All ID generation is deterministic using SHA-256, ensuring the same entity
always gets the same ID across sessions and evaluation runs.
"""

from __future__ import annotations

from hashlib import sha256


def default_document_id_strategy(content: str) -> str:
    """Create a stable document ID from content using SHA-256 hex digest."""
    return sha256(content.encode("utf-8")).hexdigest()


def default_query_id_strategy(text: str) -> str:
    """Create a stable query ID from text using SHA-256 hex digest."""
    return sha256(text.encode("utf-8")).hexdigest()


def default_perspective_id_strategy(perspective_text: str) -> str:
    """Create a stable perspective/user profile ID using SHA-256 hex digest."""
    return sha256(perspective_text.encode("utf-8")).hexdigest()


def default_query_evaluation_criterias_id_strategy(
    query_id: str,
    perspective_id: str,
) -> str:
    """Create a stable ID for QueryEvaluationCriteriaCache from query+perspective IDs."""
    return sha256(f"{query_id}:{perspective_id}".encode()).hexdigest()


def default_document_statistics_strategy(
    query_id: str,
    perspective_id: str,
    document_id: str,
) -> str:
    """Create a stable ID for DocumentRelevanceEvaluationCache from query+perspective+document IDs."""
    return sha256(f"{query_id}:{perspective_id}:{document_id}".encode()).hexdigest()
