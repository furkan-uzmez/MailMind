"""
Abstract base class for TTS (Text-to-Speech) providers.
Defines the contract for all TTS implementations.
"""

from abc import ABC, abstractmethod


class BaseTTSEngine(ABC):
    """
    Abstract base class for TTS engines.
    
    All TTS providers (edge-tts, ElevenLabs, pyttsx3, etc.)
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
    def speak(self, text: str) -> bool:
        """
        Speak text aloud.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def speak_async(self, text: str) -> bool:
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        pass
