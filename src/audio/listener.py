"""
Speech-to-Text module using faster-whisper.
Handles microphone input and transcription for voice commands.
"""

import queue
import threading
from typing import Optional, Callable

import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import config

console = Console()


class Listener:
    """STT engine using faster-whisper with microphone input."""
    
    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None
    ):
        self._model_size = model_size or config.audio.whisper_model
        self._device = device or config.audio.whisper_device
        self._model = None
        self._sample_rate = 16000
        self._is_listening = False
        self._audio_queue: queue.Queue = queue.Queue()
        
    def _init_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                
                console.print(f"[cyan]🎤 Loading Whisper model ({self._model_size})...[/cyan]")
                
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type="int8"  # Optimized for speed
                )
                
                console.print("[green]✅ Whisper model loaded![/green]")
                
            except ImportError:
                console.print("[red]❌ faster-whisper not installed[/red]")
                console.print("[yellow]💡 Run: pip install faster-whisper[/yellow]")
                raise
            except Exception as e:
                console.print(f"[red]❌ Failed to load Whisper: {e}[/red]")
                raise
    
    def listen(
        self,
        duration: float = 5.0,
        prompt: str = "🎤 Listening...",
        silence_threshold: float = 0.01
    ) -> str:
        """
        Listen for voice input and transcribe.
        
        Args:
            duration: Maximum recording duration in seconds
            prompt: Prompt to display while listening
            silence_threshold: Audio level below which is considered silence
            
        Returns:
            Transcribed text or empty string if nothing detected
        """
        self._init_model()
        
        try:
            import sounddevice as sd
        except ImportError:
            console.print("[red]❌ sounddevice not installed[/red]")
            return ""
        
        console.print(f"\n[bold cyan]{prompt}[/bold cyan] (speak now, {duration}s)")
        
        try:
            # Record audio
            recording = sd.rec(
                int(duration * self._sample_rate),
                samplerate=self._sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            # Check if we got meaningful audio
            audio_level = np.abs(recording).mean()
            if audio_level < silence_threshold:
                console.print("[dim]🔇 No speech detected[/dim]")
                return ""
            
            console.print("[cyan]🔄 Transcribing...[/cyan]")
            
            # Transcribe
            audio = recording.flatten()
            segments, info = self._model.transcribe(
                audio,
                language="en",
                beam_size=5,
                vad_filter=True  # Filter out non-speech
            )
            
            # Collect transcription
            text = " ".join(segment.text for segment in segments).strip()
            
            if text:
                console.print(f"[green]📝 You said: \"{text}\"[/green]")
            else:
                console.print("[dim]🔇 Could not transcribe audio[/dim]")
            
            return text
            
        except Exception as e:
            console.print(f"[red]❌ Recording error: {e}[/red]")
            return ""
    
    def listen_continuous(
        self,
        callback: Callable[[str], bool],
        wake_word: Optional[str] = None,
        silence_timeout: float = 2.0
    ):
        """
        Continuously listen and call callback with transcribed text.
        
        Args:
            callback: Function that receives transcribed text, returns False to stop
            wake_word: Optional wake word to filter (e.g., "hey assistant")
            silence_timeout: Seconds of silence before processing
        """
        self._init_model()
        self._is_listening = True
        
        console.print("[bold green]🎤 Continuous listening started[/bold green]")
        if wake_word:
            console.print(f"[dim]Wake word: \"{wake_word}\"[/dim]")
        console.print("[dim]Say 'stop listening' to quit[/dim]")
        
        try:
            while self._is_listening:
                text = self.listen(duration=5.0, prompt="🎤 Ready")
                
                if not text:
                    continue
                
                # Check for stop command
                if "stop listening" in text.lower():
                    console.print("[yellow]👋 Stopping listener...[/yellow]")
                    break
                
                # Check wake word if set
                if wake_word and wake_word.lower() not in text.lower():
                    continue
                
                # Call the callback
                if not callback(text):
                    break
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Interrupted[/yellow]")
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
            console.print(f"[dim]   Channels: {device_info['max_input_channels']}[/dim]")
            console.print(f"[dim]   Sample rate: {device_info['default_samplerate']} Hz[/dim]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ No microphone found: {e}[/red]")
            return False


# Quick test
if __name__ == "__main__":
    listener = Listener()
    
    console.print("[bold]Testing microphone...[/bold]")
    if listener.test_microphone():
        console.print("\n[bold]Testing transcription...[/bold]")
        text = listener.listen(duration=5.0)
        if text:
            console.print(f"[bold green]Transcribed: {text}[/bold green]")
