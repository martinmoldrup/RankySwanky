

import pathlib
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMClient(ABC):
    """Interface for LLM/NLP operations (e.g., OpenAI)."""

    @abstractmethod
    async def chat_completion(self, prompt: str, model: str = "gpt-4") -> str:
        ...

    @abstractmethod
    async def chat_completion_with_history(self, messages: list[dict], model: str = "gpt-4", parameters: dict = {}) -> str:
        ...

    @abstractmethod
    async def execute_prompty(self, prompt_path: pathlib.Path, inputs: dict) -> str:
        ...

    @abstractmethod
    async def stream_openai_answer(self, messages: list[dict], model: str, parameters: dict) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def generate_embedding(self, input_text: str, model: str) -> list[float]:
        ...
