"""
Factory for creating LLM engine instances.
Selects the appropriate provider based on configuration.
"""

import os
from typing import Optional, Type

from rich.console import Console

from .base import BaseLLMEngine

console = Console()

# Registry of available providers
_PROVIDERS: dict[str, Type[BaseLLMEngine]] = {}


def _register_providers():
    """Register all available LLM providers."""
    global _PROVIDERS
    
    # Ollama (local)
    try:
        from .ollama import OllamaEngine
        _PROVIDERS["ollama"] = OllamaEngine
    except ImportError:
        pass
    
    # OpenAI (cloud)
    try:
        from .openai import OpenAIEngine
        _PROVIDERS["openai"] = OpenAIEngine
    except ImportError:
        pass

    # Gemini (cloud)
    try:
        from .gemini import GeminiEngine
        _PROVIDERS["gemini"] = GeminiEngine
    except ImportError:
        pass


def get_available_providers() -> list[str]:
    """Get list of available LLM provider names."""
    if not _PROVIDERS:
        _register_providers()
    return list(_PROVIDERS.keys())


def create_llm_engine(
    provider: Optional[str] = None,
    **kwargs
) -> BaseLLMEngine:
    """
    Create an LLM engine instance based on provider name.
    
    Args:
        provider: Provider name ('ollama', 'openai'). 
                  If None, uses LLM_PROVIDER env var or defaults to 'ollama'.
        **kwargs: Additional arguments passed to the provider constructor.
        
    Returns:
        Instance of the selected LLM engine.
        
    Raises:
        ValueError: If provider is not available.
    """
    if not _PROVIDERS:
        _register_providers()
    
    # Determine provider
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    provider = provider.lower()
    
    if provider not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available providers: {available}"
        )
    
    console.print(f"[dim]🔧 Using LLM provider: {provider}[/dim]")
    
    engine_class = _PROVIDERS[provider]
    return engine_class(**kwargs)


# Convenience alias for backward compatibility
def LLMEngine(**kwargs) -> BaseLLMEngine:
    """Create default LLM engine (backward compatible)."""
    return create_llm_engine(**kwargs)
