"""
Store models for doing caching and persistence for the retrieval system.

To ensure expensive operations like comparing documents, doing text embeddings or calculating relevance scores are not repeated unnecessarily,
"""
from datetime import datetime
from typing import Any
from sqlmodel import JSON, Column, Field, SQLModel


class Document(SQLModel, table=True):
    """A single document to be used in the retrieval system."""

    __tablename__ = "documents"

    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the document."""

    content: str
    """The content of the document."""

    embedding_vector: list[float] = Field(default_factory=list, sa_column=Column(JSON))
    """The vector embeddings of the document."""

    # metadata: dict[str, str] = Field(
    #     default_factory=dict, sa_column=Column(JSON)
    # )
    # """Optional metadata for the document, e.g. title, author, etc."""

    hash: str
    """A unique hash for the document, used to identify it in the retrieval system."""

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the document was created or last updated."""


class Query(SQLModel, table=True):
    """A single query (a search request) to be used in the retrieval system."""

    __tablename__ = "queries"

    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the query."""

    text: str
    """The text of the query."""

    embedding_vector: list[float] = Field(default_factory=list, sa_column=Column(JSON))
    """The vector embeddings of the query."""

    # metadata: Optional[dict[str, str]] = None
    # """Optional metadata for the query, e.g. user ID, timestamp, etc."""

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the query was created."""


class UserProfile(SQLModel, table=True):
    """A user profile representing a perspective from which queries and documents can be evaluated."""

    __tablename__ = "user_profiles"

    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the user profile."""

    name: str
    """The name of the user profile or perspective."""

    description: str
    """A description of the user profile or perspective."""

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the user profile was created."""


class QueryEvaluationCriteriaCache(SQLModel, table=True):  # Has data, Approach 2
    """Parameters for generating and evaluating questions."""

    __tablename__ = "query_evaluation_criteria_cache"

    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the parameters record."""

    query_id: str = Field(foreign_key="queries.id")
    """The ID of the original query/question."""

    user_profile_id: str = Field(foreign_key="user_profiles.id")
    """The perspective from which the question is generated."""

    query_rewrites: list[str] = Field(
        default_factory=list,
        description="List of rewritten questions based on the original question and perspective.",
        sa_column=Column(JSON),
    )
    evaluation_criteria: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of weighted properties with name and normalized weight.",
        sa_column=Column(JSON),
    )

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the evaluation was performed."""


class DocumentRelevanceEvaluationCache(SQLModel, table=True):  # Has data, Approach 2
    """Stores the evaluation of document metrics for a specific question."""

    __tablename__ = "document_relevance_evaluation_cache"

    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the evaluation record."""

    document_id: str = Field(foreign_key="documents.id")
    """FOREIGN_KEY:Document.id. The ID of the document being evaluated."""

    user_profile_id: str = Field(foreign_key="user_profiles.id")
    """FOREIGN_KEY:UserProfile.id. The perspective from which the document is evaluated."""

    query_id: str = Field(foreign_key="queries.id")
    """FOREIGN_KEY:Query.id. The ID of the query/question."""

    relevance_score: float
    """The relevance score of the document for the question."""

    query_evaluation_criteria_id: str = Field(
        foreign_key="query_evaluation_criteria_cache.id",
    )
    """FOREIGN_KEY:QueryEvaluationCriteriaCache.id. The ID of the query evaluation criteria."""

    criteria_met: dict[str, bool] = Field(
        default_factory=dict,
        description="A dictionary mapping properties of a good document to boolean values indicating whether the document possesses each property.",
        sa_column=Column(JSON),
    )

    # novelty_score: float
    # """The novelty score of the document for the question."""

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the evaluation was performed."""

# class SourcesComparisonResult(enum.Enum):
#     """Enum for the source of a comparison result between documents."""

#     LLM_JUDGE = "llm_judge"
#     """The comparison was made by an LLM judge."""

#     TRANSITIVE_INFERENCE = "transitive_inference"
#     """The property has been found by Transitive inference."""

#     HUMAN_JUDGE = "human_judge"
#     """The comparison was made by a human judge."""


# class DocumentsInferedComparisonResultCache(SQLModel, table=True):  # Approach 3
#     """A result of comparing two documents."""

#     __tablename__ = "documents_infered_comparison_results"

#     id: str = Field(primary_key=True)
#     """PRIMARY_KEY. A unique identifier for the comparison result."""

#     id_document_object: str = Field(foreign_key="documents.id")
#     """FOREIGN_KEY:Document.id. The ID of the document object being compared."""

#     predicate: str = "isJudgedMoreRelevantThan"
#     """The predicate used for comparison, e.g. 'isJudgedMoreRelevantThan'."""

#     id_document_subject: str = Field(foreign_key="documents.id")
#     """FOREIGN_KEY:Document.id. The ID of the document subject being compared."""

#     source: SourcesComparisonResult
#     """The source of the comparison result, e.g. LLM judge, transitive inference, or human judge."""

#     timestamp: datetime = Field(default_factory=datetime.now)
#     """The timestamp when the comparison was made."""


# class RelevanceScore(SQLModel, table=True):  # For approach 1
#     """A relevance score for a document in the context of a query."""

#     __tablename__ = "relevance_scores"
#     id: str = Field(primary_key=True)
#     """PRIMARY_KEY. A unique identifier for the relevance score."""

#     document_id: str = Field(foreign_key="documents.id")
#     """FOREIGN_KEY:Document.id. The ID of the document being scored."""

#     query_id: str = Field(foreign_key="queries.id")
#     """FOREIGN_KEY:Query.id. The ID of the query."""

#     score: float
#     """The relevance score of the document for the query."""

#     prompt_used: str
#     """The prompt used to generate the relevance score."""

#     timestamp: datetime = Field(default_factory=datetime.now)
#     """The timestamp when the score was calculated."""


# class RetrievalSystemRoot(SQLModel, table=True):
#     """Root model for the retrieval system."""
#     documents: list[Document] = Field(default_factory=list)
#     """List of documents in the retrieval system."""

#     queries: list[Query] = Field(default_factory=list)
#     """List of queries in the retrieval system."""

#     relevance_scores: list[RelevanceScore] = Field(default_factory=list)
#     """List of relevance scores for documents in the context of queries."""

#     comparison_results: list[ComparisonResult] = Field(default_factory=list)
#     """List of comparison results between documents."""

if __name__ == "__main__":
    from eralchemy import render_er
    render_er(
        input=SQLModel.metadata,
        output="docs/caching_models.png",
    )
