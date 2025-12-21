"""Audio modules: TTS speaker and STT listener."""

from .tts import (
    BaseTTSEngine,
    create_tts_engine,
    get_available_providers as get_tts_providers,
)
from .stt import (
    BaseSTTEngine,
    create_stt_engine,
    get_available_providers as get_stt_providers,
)


# Backward compatible aliases
def Speaker(**kwargs):
    """Create default TTS engine."""
    return create_tts_engine(**kwargs)


def Listener(**kwargs):
    """Create default STT engine."""
    return create_stt_engine(**kwargs)


__all__ = [
    "BaseTTSEngine",
    "BaseSTTEngine",
    "Speaker",
    "Listener",
    "create_tts_engine",
    "create_stt_engine",
    "get_tts_providers",
    "get_stt_providers",
]
