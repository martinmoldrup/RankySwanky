"""Test-local stubs and fixtures for mapping tests.

Provides lightweight substitutes for optional heavy dependencies and stubs the
top-level package to avoid executing heavy imports during test collection.
"""
from __future__ import annotations

import sys
import types
import os

# Stub for rankyswanky top-level package to avoid executing its __init__.py,
# but only when the real package is not already importable (e.g. not installed).
if "rankyswanky" not in sys.modules:
    try:
        import rankyswanky  # noqa: F401 - triggers real __init__.py if installed
    except ImportError:
        pkg = types.ModuleType("rankyswanky")
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rankyswanky"))
        pkg.__path__ = [root_dir]  # type: ignore[attr-defined]
        sys.modules["rankyswanky"] = pkg

# Stub for langchain_openai to avoid optional dependency during tests
mod = types.ModuleType("langchain_openai")

class AzureChatOpenAI:  # type: ignore
    def __init__(self, *args, **kwargs) -> None:
        pass

class AzureOpenAIEmbeddings:  # type: ignore
    def __init__(self, *args, **kwargs) -> None:
        pass

setattr(mod, "AzureChatOpenAI", AzureChatOpenAI)
setattr(mod, "AzureOpenAIEmbeddings", AzureOpenAIEmbeddings)

sys.modules.setdefault("langchain_openai", mod)
