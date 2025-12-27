"""
OpenAI Whisper API STT provider.
Cloud-based transcription using OpenAI's Whisper API.
"""

import os
import tempfile
from typing import Callable, Optional

import numpy as np
from rich.console import Console

from .base import BaseSTTEngine

console = Console()


class OpenAIWhisperEngine(BaseSTTEngine):
    """Cloud STT engine using OpenAI Whisper API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client = None
        self._sample_rate = 16000
        self._is_listening = False
        
    @property
    def provider_name(self) -> str:
        return "openai_whisper"
    
    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                console.print("[red]❌ openai package not installed[/red]")
                raise
        return self._client
    
    def is_available(self) -> bool:
        """Check if OpenAI API is configured."""
        if not self._api_key:
            console.print("[yellow]⚠️  OPENAI_API_KEY not set[/yellow]")
            return False
        
        try:
            self._get_client()
            console.print("[green]✅ OpenAI Whisper API ready[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ OpenAI not available: {e}[/red]")
            return False
    
    def listen(
        self,
        max_duration: float = 30.0,
        silence_timeout: float = 2.0,
        prompt: str = "🎤 Listening...",
    ) -> str:
        """Listen and transcribe using OpenAI Whisper API."""
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wav
        except ImportError:
            console.print("[red]❌ sounddevice/scipy not installed[/red]")
            return ""
        
        console.print(f"\n[bold cyan]{prompt}[/bold cyan] (speak now, max {max_duration}s)")
        
        try:
            # Note: Cloud provider doesn't support VAD yet, using fixed duration
            recording = sd.rec(
                int(max_duration * self._sample_rate),
                samplerate=self._sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            audio_level = np.abs(recording).mean()
            if audio_level < silence_threshold:
                console.print("[dim]🔇 No speech detected[/dim]")
                return ""
            
            console.print("[cyan]🔄 Transcribing (OpenAI)...[/cyan]")
            
            # Save to temp WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav.write(f.name, self._sample_rate, recording)
                temp_path = f.name
            
            # Send to OpenAI
            client = self._get_client()
            with open(temp_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            text = response.text.strip()
            
            # Cleanup
            import os
            os.unlink(temp_path)
            
            if text:
                console.print(f"[green]📝 You said: \"{text}\"[/green]")
            
            return text
            
        except Exception as e:
            console.print(f"[red]❌ Transcription error: {e}[/red]")
            return ""
    
    def listen_continuous(
        self,
        callback: Callable[[str], bool],
        wake_word: Optional[str] = None,
    ):
        """Continuously listen and call callback."""
        self._is_listening = True
        
        console.print("[bold green]🎤 Continuous listening (OpenAI) started[/bold green]")
        
        try:
            while self._is_listening:
                text = self.listen(duration=5.0, prompt="🎤 Ready")
                
                if not text:
                    continue
                
                if "stop listening" in text.lower():
                    break
                
                if wake_word and wake_word.lower() not in text.lower():
                    continue
                
                if not callback(text):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self._is_listening = False
    
    def stop(self):
        """Stop continuous listening."""
        self._is_listening = False
    
    def test_microphone(self) -> bool:
        """Test if microphone is working."""
        try:
            import sounddevice as sd
            device_info = sd.query_devices(kind="input")
            console.print(f"[green]✅ Microphone: {device_info['name']}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ No microphone: {e}[/red]")
            return False
