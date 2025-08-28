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

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from rankyswanky.models.caching_models import (
	Document as PersistedDocument,
	Query as PersistedQuery,
	RelevanceScore as PersistedRelevanceScore,
	GenAndEvaluateQuestionParameters as PersistedGenEvalParams,
)
from rankyswanky.models.retrieval_evaluation_models import (
	QueryResults,
	RetrievedDocument,
	RetrievedDocumentMetrics,
	SearchEvaluationRun,
)
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


def default_document_hash_strategy(content: str, embedding_vector: Optional[List[float]] = None) -> str:
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


def default_gen_eval_id_strategy(query_id: str, perspective_id: str) -> str:
	"""Create a stable primary key for GenAndEvaluateQuestionParameters from query+perspective IDs."""
	return sha256(f"{query_id}:{perspective_id}".encode("utf-8")).hexdigest()

# -----------------------------
# Mapping contexts
# -----------------------------

@dataclass
class MappingContext:
	"""Holds state while mapping a run to avoid duplicates and keep stable IDs."""

	document_id_by_content: Dict[str, str]
	query_id_by_text: Dict[str, str]

	def __init__(self) -> None:
		self.document_id_by_content = {}
		self.query_id_by_text = {}


# -----------------------------
# Domain -> Persistence mapping
# -----------------------------

def map_retrieved_document_to_persisted_document(
	rd: RetrievedDocument,
	*,
	id_strategy: Callable[[str], str] = default_document_id_strategy,
	hash_strategy: Callable[[str, Optional[List[float]]], str] = default_document_hash_strategy,
	timestamp_factory: Callable[[], datetime] = _utcnow,
) -> PersistedDocument:
	"""Map a domain RetrievedDocument to a persistable Document.

	Inputs
	- rd: RetrievedDocument from the domain layer.

	Output
	- PersistedDocument ready for SQLModel persistence.
	"""
	content: str = rd.document_content
	embedding: List[float] = rd.embedding_vector or []
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


def map_relevance_to_persisted_scores(
	qr: QueryResults,
	*,
	query_id: str,
	document_id_by_content: Dict[str, str],
	prompt_used: str = "",
	timestamp_factory: Callable[[], datetime] = _utcnow,
) -> List[PersistedRelevanceScore]:
	"""Create RelevanceScore rows from a domain QueryResults object.

	The mapping uses RetrievedDocumentMetrics.relevance as the score when present.
	Documents without metrics are skipped.
	"""
	scores: List[PersistedRelevanceScore] = []
	for rd in qr.retrieved_documents:
		metrics: Optional[RetrievedDocumentMetrics] = rd.retrieved_document_metrics
		if metrics is None:
			continue
		doc_content: str = rd.document_content
		document_id: Optional[str] = document_id_by_content.get(doc_content)
		if not document_id:
			# If the document wasn't mapped yet, derive it on the fly for consistency
			document_id = default_document_id_strategy(doc_content)
		# Create a stable row ID based on query/doc to allow upsert-like behavior
		compound_key: str = sha256(f"{query_id}:{document_id}:{prompt_used}".encode("utf-8")).hexdigest()
		scores.append(
			PersistedRelevanceScore(
				id=compound_key,
				document_id=document_id,
				query_id=query_id,
				score=metrics.relevance,
				prompt_used=prompt_used,
				timestamp=timestamp_factory(),
			)
		)
	return scores


def map_search_evaluation_run_to_persistence(
	run: SearchEvaluationRun,
	*,
	prompt_used: str = "",
	id_doc_strategy: Callable[[str], str] = default_document_id_strategy,
	id_query_strategy: Callable[[str], str] = default_query_id_strategy,
	hash_strategy: Callable[[str, Optional[List[float]]], str] = default_document_hash_strategy,
	timestamp_factory: Callable[[], datetime] = _utcnow,
) -> Tuple[List[PersistedDocument], List[PersistedQuery], List[PersistedRelevanceScore]]:
	"""Map a SearchEvaluationRun into persistence-layer entities.

	Returns three lists with deduplicated Documents and Queries, and all RelevanceScores.
	"""
	ctx = MappingContext()
	documents_by_id: Dict[str, PersistedDocument] = {}
	queries_by_id: Dict[str, PersistedQuery] = {}
	all_scores: List[PersistedRelevanceScore] = []

	for qr in run.per_query_results:
		# Map query
		pq = map_query_results_to_persisted_query(qr, id_strategy=id_query_strategy, timestamp_factory=timestamp_factory)
		queries_by_id.setdefault(pq.id, pq)
		ctx.query_id_by_text.setdefault(qr.query, pq.id)

		# Map documents for this query and collect IDs
		for rd in qr.retrieved_documents:
			pd = map_retrieved_document_to_persisted_document(
				rd,
				id_strategy=id_doc_strategy,
				hash_strategy=hash_strategy,
				timestamp_factory=timestamp_factory,
			)
			documents_by_id.setdefault(pd.id, pd)
			ctx.document_id_by_content.setdefault(rd.document_content, pd.id)

		# Map scores for this query
		query_id = queries_by_id[pq.id].id
		scores = map_relevance_to_persisted_scores(
			qr,
			query_id=query_id,
			document_id_by_content=ctx.document_id_by_content,
			prompt_used=prompt_used,
			timestamp_factory=timestamp_factory,
		)
		all_scores.extend(scores)

	return list(documents_by_id.values()), list(queries_by_id.values()), all_scores


# -----------------------------
# Persistence -> Domain mapping
# -----------------------------

def map_persisted_to_query_results(
	query: PersistedQuery,
	documents: Iterable[PersistedDocument],
	scores: Iterable[PersistedRelevanceScore],
) -> QueryResults:
	"""Map persisted rows back to a domain QueryResults object.

	Documents are ranked by score (desc). If multiple scores exist per document, the highest is used.
	"""
	# Build best score per document
	best_by_doc: Dict[str, float] = {}
	for s in scores:
		if s.query_id != query.id:
			continue
		if s.document_id not in best_by_doc or s.score > best_by_doc[s.document_id]:
			best_by_doc[s.document_id] = s.score

	# Filter and sort provided documents by their best score
	relevant_docs: List[Tuple[PersistedDocument, float]] = []
	doc_index: Dict[str, PersistedDocument] = {d.id: d for d in documents}
	for doc_id, score in best_by_doc.items():
		doc = doc_index.get(doc_id)
		if doc is not None:
			relevant_docs.append((doc, score))

	relevant_docs.sort(key=lambda t: t[1], reverse=True)

	retrieved: List[RetrievedDocument] = []
	for idx, (doc, score) in enumerate(relevant_docs, start=1):
		metrics = RetrievedDocumentMetrics(relevance=score, novelty=0.0)
		retrieved.append(
			RetrievedDocument(
				document_content=doc.content,
				rank=idx,
				embedding_vector=doc.embedding_vector,
				retrieved_document_metrics=metrics,
			)
		)

	return QueryResults(
		query=query.text,
		retrieved_documents=retrieved,
		query_metrics=None,
		retrieval_time_ms=0,
	)

# -----------------------------
# Gen/Eval question parameters mapping
# -----------------------------

@runtime_checkable
class CombinedOutputLike(Protocol):
	"""Protocol for compatibility with CombinedOutput model in utils module."""

	question: str
	perspective: str
	rewritten_questions: List[str]
	properties_of_a_good_document_containing_all_perspectives: List[str]


def map_combined_output_to_gen_and_evaluate_params(
	combined: CombinedOutputLike,
	*,
	query_id_strategy: Callable[[str], str] = default_query_id_strategy,
	perspective_id_strategy: Callable[[str], str] = default_perspective_id_strategy,
	gen_eval_id_strategy: Callable[[str, str], str] = default_gen_eval_id_strategy,
) -> PersistedGenEvalParams:
	"""Map a CombinedOutput-like object to GenAndEvaluateQuestionParameters.

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
		perspective_id=perspective_id,
		rewritten_questions=list(combined.rewritten_questions),
		properties_of_a_good_document_containing_all_perspectives=list(
			combined.properties_of_a_good_document_containing_all_perspectives
		),
	)


