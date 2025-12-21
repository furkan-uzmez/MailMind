"""
Text-to-Speech module using edge-tts with pyttsx3 fallback.
Provides async and sync speech output for reading email summaries.
"""

import asyncio
import io
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console

from src.config import config

console = Console()


class Speaker:
    """TTS engine with edge-tts (online) and pyttsx3 (offline) support."""
    
    def __init__(self, voice: Optional[str] = None):
        self._voice = voice or config.audio.tts_voice
        self._offline_engine = None
        self._use_offline = False
        
    def _init_offline(self):
        """Initialize offline pyttsx3 engine."""
        if self._offline_engine is None:
            try:
                import pyttsx3
                self._offline_engine = pyttsx3.init()
                self._offline_engine.setProperty("rate", 175)  # Speed
                console.print("[dim]📢 Using offline TTS (pyttsx3)[/dim]")
            except Exception as e:
                console.print(f"[red]❌ Offline TTS init failed: {e}[/red]")
    
    async def speak_async(self, text: str) -> bool:
        """
        Speak text asynchronously using edge-tts.
        Non-blocking - runs TTS in background.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        if not text.strip():
            return False
        
        try:
            import edge_tts
            
            console.print(f"[cyan]🔊 Speaking...[/cyan]")
            
            communicate = edge_tts.Communicate(text, self._voice)
            
            # Create temp file for audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            await communicate.save(temp_path)
            
            # Play the audio
            await self._play_audio_async(temp_path)
            
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
            
            return True
            
        except ImportError:
            console.print("[yellow]⚠️  edge-tts not installed, using offline TTS[/yellow]")
            return self.speak_sync(text)
        except Exception as e:
            console.print(f"[yellow]⚠️  edge-tts failed: {e}, falling back to offline[/yellow]")
            return self.speak_sync(text)
    
    async def _play_audio_async(self, filepath: str):
        """Play audio file asynchronously."""
        try:
            import subprocess
            
            # Try different audio players
            players = ["mpv", "ffplay", "aplay", "paplay"]
            
            for player in players:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        player, "-nodisp" if player == "ffplay" else filepath,
                        filepath if player == "ffplay" else "",
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    # Fix the command based on player
                    if player == "ffplay":
                        proc = await asyncio.create_subprocess_exec(
                            "ffplay", "-nodisp", "-autoexit", filepath,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                    elif player == "mpv":
                        proc = await asyncio.create_subprocess_exec(
                            "mpv", "--no-video", filepath,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                    else:
                        proc = await asyncio.create_subprocess_exec(
                            player, filepath,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                    await proc.wait()
                    return
                except FileNotFoundError:
                    continue
            
            console.print("[yellow]⚠️  No audio player found (install mpv or ffplay)[/yellow]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Audio playback error: {e}[/yellow]")
    
    def speak_sync(self, text: str) -> bool:
        """
        Speak text synchronously using pyttsx3 (offline).
        Blocking - waits for speech to complete.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        if not text.strip():
            return False
        
        self._init_offline()
        
        if self._offline_engine is None:
            console.print("[red]❌ No TTS engine available[/red]")
            return False
        
        try:
            console.print(f"[cyan]🔊 Speaking (offline)...[/cyan]")
            self._offline_engine.say(text)
            self._offline_engine.runAndWait()
            return True
        except Exception as e:
            console.print(f"[red]❌ TTS error: {e}[/red]")
            return False
    
    def speak(self, text: str) -> bool:
        """
        Speak text (convenience wrapper).
        Uses async edge-tts if possible, falls back to sync pyttsx3.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        try:
            return asyncio.run(self.speak_async(text))
        except Exception:
            return self.speak_sync(text)
    
    @staticmethod
    def list_voices():
        """List available edge-tts voices."""
        async def _list():
            try:
                import edge_tts
                voices = await edge_tts.list_voices()
                return voices
            except Exception:
                return []
        
        voices = asyncio.run(_list())
        
        # Filter to English voices
        en_voices = [v for v in voices if v["Locale"].startswith("en-")]
        
        console.print("[bold]Available English Voices:[/bold]")
        for v in en_voices[:10]:
            console.print(f"  • {v['ShortName']}: {v['Gender']}")
        
        return en_voices


# Quick test
if __name__ == "__main__":
    speaker = Speaker()
    
    # Test with a sample sentence
    test_text = "Hello! You have 3 important emails today. The first one is from your boss about the Q4 budget meeting."
    
    console.print("[bold]Testing TTS...[/bold]")
    speaker.speak(test_text)
