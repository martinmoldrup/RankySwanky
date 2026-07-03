"""
Infrastructure implementation for communicating with OpenAI LLM models via external API.

Adds both synchronous and asynchronous client support. The async client mirrors the synchronous
interface but exposes an ``stream_openai_answer_async`` coroutine returning an async iterator of tokens.
"""
from __future__ import annotations

import logging
import pathlib
import prompty
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from collections.abc import AsyncIterator
from openai import AsyncOpenAI, AsyncStream, omit
from openai.types.responses import ResponseStreamEvent, ResponseTextDeltaEvent
from rankyswanky.models.adapter_models import LLMClient
from rankyswanky.models.connections import AzureOpenAIConnection

logger = logging.getLogger(__name__)

BEARER_TOKEN_PROVIDER_SCOPE = "https://cognitiveservices.azure.com/.default"
"""Scope for Azure Cognitive Services used by the bearer token provider."""


class OpenAILLMClient(LLMClient):
    """
    Asynchronous Azure OpenAI client wrapper.

    Provides async chat completion and streaming compatible with ``async for``.
    """

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        """Initialize the OpenAI client with Azure Managed Identity authentication."""
        default_credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(default_credential, BEARER_TOKEN_PROVIDER_SCOPE) if api_key is None else api_key
        if isinstance(token_provider, str):
            logger.warning("Using API key for OpenAI client; this should only be used for testing purposes.")
            # TODO: Check that api key credentials is not used in production or when running in Azure environment, and raise error if it is
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=token_provider,
            max_retries=10,
            timeout=60,
        )

    @classmethod
    def from_connection(cls, config: AzureOpenAIConnection) -> OpenAILLMClient:
        return cls(
            base_url=config.api_base,
            api_key=config.api_key.get_secret_value() if config.api_key else None,
        )

    async def chat_completion(self, prompt: str, model: str = "gpt-4") -> str:
        """Calls the OpenAI API to generate a plan based on the given prompt."""
        response = await self.chat_completion_with_history(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return response

    async def chat_completion_with_history(self, messages: list, model: str = "gpt-4", parameters: dict = {}) -> str:
        response = await self.client.responses.create(
            stream=False,
            model=model,
            input=messages,
            temperature=parameters.get("temperature", omit),
            max_output_tokens=parameters.get("max_output_tokens", omit),
        )
        return response.output_text

    async def execute_prompty(self, prompt_path: pathlib.Path, inputs: dict) -> str:
        """Execute the prompty prompt."""
        prompt = prompty.load(prompt_path)
        messages: list[dict] = prompty.prepare(prompt, inputs)
        response = await self.chat_completion_with_history(
            messages=messages,
            model=prompt.model.configuration["azure_deployment"],
            parameters=prompt.model.parameters,
        )
        return response

    async def stream_openai_answer(self, messages: list, model: str, parameters: dict) -> AsyncIterator[str]:
        """Async streaming interface returning content chunks as they arrive."""
        async_stream: AsyncStream[ResponseStreamEvent] = await self.client.responses.create(
            stream=True,
            input=messages,
            model=model,
            temperature=parameters.get("temperature", omit),
            max_output_tokens=parameters.get("max_output_tokens", omit),
        )

        async def generator() -> AsyncIterator[str]:
            async for event in async_stream:
                if isinstance(event, ResponseTextDeltaEvent):
                    yield event.delta
                else:
                    # TODO: Figure out of we should handle any of the other event types
                    continue

        return generator()

    async def generate_embedding(self, input_text: str, model: str) -> list[float]:
        """Generate embedding for the given input text."""
        response = await self.client.embeddings.create(
            model=model,
            input=input_text,
        )
        return response.data[0].embedding


if __name__ == "__main__":
    import asyncio
    from gwc_ai_services.configurations import get_gwc_ai_services_settings
    config = get_gwc_ai_services_settings()
    llm_client = OpenAILLMClient.from_connection(
        config.get_azure_openai_connection(),
    )
    async def main() -> None:
        res = await llm_client.generate_embedding("Hello world", model="text-embedding-3-large")
        print(res)

    asyncio.run(main())
