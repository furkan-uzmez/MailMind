"""
Abstract base class for STT (Speech-to-Text) providers.
Defines the contract for all STT implementations.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class BaseSTTEngine(ABC):
    """
    Abstract base class for STT engines.
    
    All STT providers (faster-whisper, OpenAI Whisper API, Google, etc.)
    must implement this interface.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and configured."""
        pass
    
    @abstractmethod
    def listen(
        self,
        max_duration: float = 30.0,
        silence_timeout: float = 2.0,
        prompt: str = "🎤 Listening...",
    ) -> str:
        """
        Listen for voice input and transcribe with silence detection.
        
        Args:
            max_duration: Maximum recording duration in seconds
            silence_timeout: Stop recording after this many seconds of silence
            prompt: Prompt to display while listening
            
        Returns:
            Transcribed text or empty string if nothing detected
        """
        pass
    
    @abstractmethod
    def listen_continuous(
        self,
        callback: Callable[[str], bool],
        wake_word: Optional[str] = None,
    ):
        """
        Continuously listen and call callback with transcribed text.
        
        Args:
            callback: Function receiving transcribed text, returns False to stop
            wake_word: Optional wake word to filter
        """
        pass
    
    @abstractmethod
    def stop(self):
        """Stop continuous listening."""
        pass
    
    @abstractmethod
    def test_microphone(self) -> bool:
        """Test if microphone is working."""
        pass
