"""
Edge TTS provider (Microsoft Azure free tier).
High quality voices with async support.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console

from .base import BaseTTSEngine
from src.config import config

console = Console()


class EdgeTTSEngine(BaseTTSEngine):
    """TTS engine using edge-tts (Microsoft Azure)."""
    
    def __init__(self, voice: Optional[str] = None):
        self._voice = voice or config.audio.tts_voice
        self._offline_engine = None
        self._current_process = None  # Track current audio process for skipping
        
    @property
    def provider_name(self) -> str:
        return "edge"
    
    def is_available(self) -> bool:
        """Check if edge-tts is available."""
        try:
            import edge_tts
            console.print(f"[green]✅ edge-tts available (voice: {self._voice})[/green]")
            return True
        except ImportError:
            console.print("[yellow]⚠️  edge-tts not installed[/yellow]")
            return False
    
    def stop(self):
        """Stop current audio playback (used for skipping)."""
        if self._current_process:
            try:
                self._current_process.terminate()
                console.print("[dim]⏭️  Skipped[/dim]")
            except Exception:
                pass
            self._current_process = None
    
    def _init_offline_fallback(self):
        """Initialize pyttsx3 as fallback."""
        if self._offline_engine is None:
            try:
                import pyttsx3
                self._offline_engine = pyttsx3.init()
                self._offline_engine.setProperty("rate", 175)
            except Exception:
                pass
    
    async def speak_async(self, text: str) -> bool:
        """Speak text asynchronously using edge-tts."""
        if not text.strip():
            return False
        
        try:
            import edge_tts
            
            console.print("[cyan]🔊 Speaking (edge-tts)... [dim]Press Enter to skip[/dim][/cyan]")
            
            communicate = edge_tts.Communicate(text, self._voice)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            await communicate.save(temp_path)
            await self._play_audio_async(temp_path)
            
            Path(temp_path).unlink(missing_ok=True)
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠️  edge-tts failed: {e}[/yellow]")
            return self._speak_offline(text)
    
    async def _play_audio_async(self, filepath: str):
        """Play audio file asynchronously with skip support."""
        import sys
        import select
        
        try:
            players = [
                ("mpv", ["--no-video", filepath]),
                ("ffplay", ["-nodisp", "-autoexit", filepath]),
                ("aplay", [filepath]),
            ]
            
            for player, args in players:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        player, *args,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    self._current_process = proc
                    
                    # Wait for process with skip check
                    while proc.returncode is None:
                        # Check if Enter was pressed (non-blocking)
                        if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                            line = sys.stdin.readline()
                            if line.strip().lower() in ('', 'skip', 's'):
                                proc.terminate()
                                console.print("[dim]⏭️  Skipped[/dim]")
                                break
                        await asyncio.sleep(0.1)
                    
                    self._current_process = None
                    return
                except FileNotFoundError:
                    continue
            
            console.print("[yellow]⚠️  No audio player found[/yellow]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Playback error: {e}[/yellow]")
    
    def _speak_offline(self, text: str) -> bool:
        """Fallback to pyttsx3 offline TTS."""
        self._init_offline_fallback()
        
        if self._offline_engine is None:
            return False
        
        try:
            console.print("[cyan]🔊 Speaking (offline)...[/cyan]")
            self._offline_engine.say(text)
            self._offline_engine.runAndWait()
            return True
        except Exception:
            return False
    
    def speak(self, text: str) -> bool:
        """Speak text (convenience wrapper)."""
        try:
            return asyncio.run(self.speak_async(text))
        except Exception:
            return self._speak_offline(text)
