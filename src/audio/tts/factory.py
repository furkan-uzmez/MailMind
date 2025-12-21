"""
Factory for creating TTS engine instances.
"""

import os
from typing import Optional, Type

from rich.console import Console

from .base import BaseTTSEngine

console = Console()

_PROVIDERS: dict[str, Type[BaseTTSEngine]] = {}


def _register_providers():
    """Register available TTS providers."""
    global _PROVIDERS
    
    # Edge TTS (default, free)
    try:
        from .edge import EdgeTTSEngine
        _PROVIDERS["edge"] = EdgeTTSEngine
    except ImportError:
        pass
    
    # ElevenLabs (premium quality)
    try:
        from .elevenlabs import ElevenLabsEngine
        _PROVIDERS["elevenlabs"] = ElevenLabsEngine
    except ImportError:
        pass


def get_available_providers() -> list[str]:
    """Get list of available TTS providers."""
    if not _PROVIDERS:
        _register_providers()
    return list(_PROVIDERS.keys())


def create_tts_engine(
    provider: Optional[str] = None,
    **kwargs
) -> BaseTTSEngine:
    """
    Create a TTS engine instance.
    
    Args:
        provider: Provider name ('edge', 'elevenlabs').
                  If None, uses TTS_PROVIDER env var or 'edge'.
        **kwargs: Additional arguments for provider.
        
    Returns:
        Instance of selected TTS engine.
    """
    if not _PROVIDERS:
        _register_providers()
    
    if provider is None:
        provider = os.getenv("TTS_PROVIDER", "edge").lower()
    
    provider = provider.lower()
    
    if provider not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(f"Unknown TTS provider: '{provider}'. Available: {available}")
    
    console.print(f"[dim]🔧 Using TTS provider: {provider}[/dim]")
    
    return _PROVIDERS[provider](**kwargs)


# Backward compatible alias
def Speaker(**kwargs) -> BaseTTSEngine:
    """Create default TTS engine."""
    return create_tts_engine(**kwargs)
