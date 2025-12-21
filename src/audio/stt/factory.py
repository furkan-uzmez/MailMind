"""
Factory for creating STT engine instances.
Selects provider based on configuration.
"""

import os
from typing import Optional, Type

from rich.console import Console

from .base import BaseSTTEngine

console = Console()

_PROVIDERS: dict[str, Type[BaseSTTEngine]] = {}


def _register_providers():
    """Register available STT providers."""
    global _PROVIDERS
    
    # Local whisper
    try:
        from .whisper import WhisperEngine
        _PROVIDERS["whisper"] = WhisperEngine
    except ImportError:
        pass
    
    # OpenAI Whisper API
    try:
        from .openai_whisper import OpenAIWhisperEngine
        _PROVIDERS["openai_whisper"] = OpenAIWhisperEngine
    except ImportError:
        pass


def get_available_providers() -> list[str]:
    """Get list of available STT providers."""
    if not _PROVIDERS:
        _register_providers()
    return list(_PROVIDERS.keys())


def create_stt_engine(
    provider: Optional[str] = None,
    **kwargs
) -> BaseSTTEngine:
    """
    Create an STT engine instance.
    
    Args:
        provider: Provider name ('whisper', 'openai_whisper').
                  If None, uses STT_PROVIDER env var or 'whisper'.
        **kwargs: Additional arguments for provider.
        
    Returns:
        Instance of selected STT engine.
    """
    if not _PROVIDERS:
        _register_providers()
    
    if provider is None:
        provider = os.getenv("STT_PROVIDER", "whisper").lower()
    
    provider = provider.lower()
    
    if provider not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(f"Unknown STT provider: '{provider}'. Available: {available}")
    
    console.print(f"[dim]🔧 Using STT provider: {provider}[/dim]")
    
    return _PROVIDERS[provider](**kwargs)


# Backward compatible alias
def Listener(**kwargs) -> BaseSTTEngine:
    """Create default STT engine."""
    return create_stt_engine(**kwargs)
