"""Abstract repository interfaces for persistence / caching models."""
from abc import ABC, abstractmethod
from typing import Optional
from rankyswanky.models.metric_calculation_models import QuestionWithRewritesAndCorrectnessProps

class QuestionWithRewritesAndCorrectnessPropsRepository(ABC):
    """Repository for QuestionWithRewritesAndCorrectnessProps persistence."""

    @abstractmethod
    def get_by_question_and_perspective(self, question: str, perspective: str) -> Optional[QuestionWithRewritesAndCorrectnessProps]:
        # ...use your mapping and pydantic_caching logic here...
        pass

    @abstractmethod
    def save(self, params: QuestionWithRewritesAndCorrectnessProps) -> None:
        # ...save logic...
        pass
