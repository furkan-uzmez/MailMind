"""
ElevenLabs TTS provider.
High-quality AI voice synthesis (cloud-based).
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console

from .base import BaseTTSEngine

console = Console()


class ElevenLabsEngine(BaseTTSEngine):
    """TTS engine using ElevenLabs API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None
    ):
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self._voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel
        self._client = None
        
    @property
    def provider_name(self) -> str:
        return "elevenlabs"
    
    def _get_client(self):
        """Lazy-load ElevenLabs client."""
        if self._client is None:
            try:
                from elevenlabs.client import ElevenLabs
                self._client = ElevenLabs(api_key=self._api_key)
            except ImportError:
                console.print("[red]❌ elevenlabs package not installed[/red]")
                console.print("[yellow]💡 Run: pip install elevenlabs[/yellow]")
                raise
        return self._client
    
    def is_available(self) -> bool:
        """Check if ElevenLabs API is configured."""
        if not self._api_key:
            console.print("[yellow]⚠️  ELEVENLABS_API_KEY not set[/yellow]")
            return False
        
        try:
            self._get_client()
            console.print("[green]✅ ElevenLabs API ready[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ ElevenLabs not available: {e}[/red]")
            return False
    
    async def speak_async(self, text: str) -> bool:
        """Speak text using ElevenLabs."""
        return await asyncio.to_thread(self.speak, text)
    
    def speak(self, text: str) -> bool:
        """Speak text using ElevenLabs API."""
        if not text.strip():
            return False
        
        try:
            client = self._get_client()
            
            console.print("[cyan]🔊 Speaking (ElevenLabs)...[/cyan]")
            
            audio = client.generate(
                text=text,
                voice=self._voice_id,
                model="eleven_monolingual_v1"
            )
            
            # Save and play audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                for chunk in audio:
                    f.write(chunk)
                temp_path = f.name
            
            self._play_audio(temp_path)
            Path(temp_path).unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ ElevenLabs error: {e}[/red]")
            return False
    
    def _play_audio(self, filepath: str):
        """Play audio file."""
        import subprocess
        
        players = ["mpv", "ffplay", "aplay"]
        
        for player in players:
            try:
                if player == "mpv":
                    subprocess.run([player, "--no-video", filepath], 
                                 capture_output=True, check=True)
                elif player == "ffplay":
                    subprocess.run([player, "-nodisp", "-autoexit", filepath],
                                 capture_output=True, check=True)
                else:
                    subprocess.run([player, filepath], 
                                 capture_output=True, check=True)
                return
            except FileNotFoundError:
                continue
