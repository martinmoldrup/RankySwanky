"""
Store models for doing caching and persistence for the retrieval system.

To ensure expensive operations like comparing documents, doing text embeddings or calculating relevance scores are not repeated unnecessarily,
"""
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column
import enum
from datetime import datetime


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

class RelevanceScore(SQLModel, table=True):
    """A relevance score for a document in the context of a query."""
    __tablename__ = "relevance_scores"
    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the relevance score."""

    document_id: str = Field(foreign_key="documents.id")
    """FOREIGN_KEY:Document.id. The ID of the document being scored."""

    query_id: str = Field(foreign_key="queries.id")
    """FOREIGN_KEY:Query.id. The ID of the query."""

    score: float
    """The relevance score of the document for the query."""

    prompt_used: str
    """The prompt used to generate the relevance score."""

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the score was calculated."""

class SourcesComparisonResult(enum.Enum):

    LLM_JUDGE = "llm_judge"
    """The comparison was made by an LLM judge."""

    TRANSITIVE_INFERENCE = "transitive_inference"
    """The property has been found by Transitive inference."""

    HUMAN_JUDGE = "human_judge"
    """The comparison was made by a human judge."""

class ComparisonResult(SQLModel, table=True):
    """A result of comparing two documents."""
    __tablename__ = "comparison_results"

    id: str = Field(primary_key=True)
    """PRIMARY_KEY. A unique identifier for the comparison result."""

    id_document_object: str = Field(foreign_key="documents.id")
    """FOREIGN_KEY:Document.id. The ID of the document object being compared."""

    predicate: str = "isJudgedMoreRelevantThan"
    """The predicate used for comparison, e.g. 'isJudgedMoreRelevantThan'."""

    id_document_subject: str
    """FOREIGN_KEY:Document.id. The ID of the document subject being compared."""

    source: SourcesComparisonResult
    """The source of the comparison result, e.g. LLM judge, transitive inference, or human judge."""

    timestamp: datetime = Field(default_factory=datetime.now)
    """The timestamp when the comparison was made."""



class GenAndEvaluateQuestionParameters(SQLModel, table=True):
    """Parameters for generating and evaluating questions."""
    __tablename__ = "gen_and_evaluate_question_parameters"

    id: str = Field(primary_key=True)
    query_id: str = Field(foreign_key="queries.id", description="The ID of the user query/question for which the question is generated.")
    perspective_id: str = Field(
        ..., description="The perspective from which the question is asked."
    )
    rewritten_questions: list[str] = Field(
        default_factory=list,
        description="List of rewritten questions based on the original question and perspective.",
        sa_column=Column(JSON)
    )
    properties_of_a_good_document_containing_all_perspectives: list[str] = Field(
        default_factory=list,
        description="List of properties that a correct answer should have.",
        sa_column=Column(JSON)
    )


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
    import erdantic as erd

    erd.draw(RelevanceScore, out="caching_models.png")