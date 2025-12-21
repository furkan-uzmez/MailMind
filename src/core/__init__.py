"""Core modules: email client and LLM engine."""

from .email_client import EmailClient, Email
from .llm import (
    BaseLLMEngine,
    EmailCategory,
    ClassificationResult,
    create_llm_engine,
    get_available_providers as get_llm_providers,
)

# Backward compatible alias
def LLMEngine(**kwargs):
    """Create default LLM engine (backward compatible)."""
    return create_llm_engine(**kwargs)

__all__ = [
    "EmailClient",
    "Email",
    "BaseLLMEngine",
    "EmailCategory",
    "ClassificationResult",
    "LLMEngine",
    "create_llm_engine",
    "get_llm_providers",
]
