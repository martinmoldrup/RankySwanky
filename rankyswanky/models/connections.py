from dataclasses import dataclass
from pydantic import SecretStr


@dataclass
class AzureOpenAIConnection:
    """Azure OpenAI configuration object."""

    name: str
    api_base: str
    api_key: SecretStr | None = None


@dataclass
class CognitiveSearchConnection:
    api_base: str
    api_key: SecretStr | None = None


@dataclass
class ProductCenterAPIConnection:
    subscription_key: SecretStr


@dataclass
class AzureLanguageConnection:
    endpoint: str
    api_key: SecretStr | None = None


@dataclass
class Neo4jConnection:
    uri: str
    username: str
    password: SecretStr
