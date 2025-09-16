import os
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

AZURE_ENDPOINT: str = os.getenv("AZURE_OPENAI_API_BASE")
AZURE_OPENAI_API_KEY: str = os.getenv("OPENAI_KEY")
AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_DEPLOYMENT_EMBEDDINGS: str = os.getenv("AZURE_DEPLOYMENT_EMBEDDINGS")
AZURE_DEPLOYMENT_CHAT: str = os.getenv("AZURE_DEPLOYMENT_CHAT")

chat_llm = AzureChatOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    azure_deployment=AZURE_DEPLOYMENT_CHAT,
    api_version=AZURE_OPENAI_API_VERSION,
)

embeddings_llm = AzureOpenAIEmbeddings(
    azure_deployment=AZURE_DEPLOYMENT_EMBEDDINGS,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    max_retries=10,
    timeout=60,
)
