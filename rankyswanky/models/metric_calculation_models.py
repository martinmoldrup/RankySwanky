
from dataclasses import dataclass

@dataclass
class QuestionWithRewrites:
    """Model to hold rewritten questions."""
    rewritten_questions: list[str]
    question: str
    perspective: str

@dataclass
class QuestionWithRewritesAndCorrectnessProps:
    """Final model combining rewritten questions and properties of a correct answer."""
    rewritten_questions: list[str]
    question: str
    perspective: str
    properties_of_a_good_document_containing_all_perspectives: list[str]

@dataclass
class RetrievedDocumentStatistics:
    """Metrics for a retrieved document with respect to a question, this is a local model for metric calculation."""
    relevance: float  # Normalized relevance score between 0 and 1
    evaluated_properties_of_a_good_document: dict[str, bool]
