"""
Local STT provider using faster-whisper.
Runs entirely on local hardware with int8 quantization for speed.
"""

from typing import Callable, Optional

import numpy as np
from rich.console import Console

from .base import BaseSTTEngine
from src.config import config

console = Console()


class WhisperEngine(BaseSTTEngine):
    """Local STT engine using faster-whisper."""
    
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
        
    @property
    def provider_name(self) -> str:
        return "whisper"
    
    def _init_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                
                console.print(f"[cyan]🎤 Loading Whisper model ({self._model_size})...[/cyan]")
                
                self._model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type="int8"
                )
                
                console.print("[green]✅ Whisper model loaded![/green]")
                
            except ImportError:
                console.print("[red]❌ faster-whisper not installed[/red]")
                console.print("[yellow]💡 Run: pip install faster-whisper[/yellow]")
                raise
    
    def is_available(self) -> bool:
        """Check if faster-whisper is available."""
        try:
            import faster_whisper
            console.print(f"[green]✅ faster-whisper available (model: {self._model_size})[/green]")
            return True
        except ImportError:
            console.print("[yellow]⚠️  faster-whisper not installed[/yellow]")
            return False
    
    def listen(
        self,
        max_duration: float = 30.0,
        silence_timeout: float = 2.0,
        prompt: str = "🎤 Listening...",
        threshold: float = 0.02
    ) -> str:
        """Listen for voice input with silence detection."""
        self._init_model()
        
        try:
            import sounddevice as sd
        except ImportError:
            console.print("[red]❌ sounddevice not installed[/red]")
            return ""
        
        console.print(f"\n[bold cyan]{prompt}[/bold cyan] (Speak now...)")
        
        audio_buffer = []
        silence_start = None
        has_started_speaking = False
        start_time = None
        
        def callback(indata, frames, time, status):
            if status:
                console.print(status)
            audio_buffer.append(indata.copy())
            
        # 1. Wait for speech to start (max 5 seconds of silence allowed at start)
        try:
            # We'll do a simple blocking loop for manual control
            # Using raw stream for better control than sd.rec
            with sd.InputStream(samplerate=self._sample_rate, channels=1, dtype=np.float32) as stream:
                import time
                start_time = time.time()
                last_speech_time = time.time()
                
                while True:
                    # Read chunk (0.1s)
                    chunk, overflow = stream.read(int(self._sample_rate * 0.1))
                    audio_buffer.append(chunk)
                    
                    # Check volume
                    volume = np.abs(chunk).mean()
                    current_time = time.time()
                    
                    if volume > threshold:
                        if not has_started_speaking:
                            console.print("[green]🗣️  Speech detected...[/green]")
                            has_started_speaking = True
                        last_speech_time = current_time
                    
                    # Logic
                    elapsed = current_time - start_time
                    silence_duration = current_time - last_speech_time
                    
                    # 1. Timeout if never started speaking
                    if not has_started_speaking and elapsed > 5.0:
                        console.print("[dim]🔇 No speech detected (timeout)[/dim]")
                        return ""
                    
                    # 2. Stop if silence after speech
                    if has_started_speaking and silence_duration > silence_timeout:
                        console.print("[dim]✅ Finished speaking[/dim]")
                        break
                        
                    # 3. Hard cutoff
                    if elapsed > max_duration:
                        console.print("[yellow]⚠️  Max duration reached[/yellow]")
                        break
                        
            # Process audio
            recording = np.concatenate(audio_buffer, axis=0)
            
            console.print("[cyan]🔄 Transcribing (local)...[/cyan]")
            
            audio = recording.flatten()
            segments, info = self._model.transcribe(
                audio,
                language="en",
                beam_size=5,
                vad_filter=True
            )
            
            text = " ".join(segment.text for segment in segments).strip()
            
            if text:
                console.print(f"[green]📝 You said: \"{text}\"[/green]")
            
            return text
            
        except Exception as e:
            console.print(f"[red]❌ Recording error: {e}[/red]")
            return ""
    
    def listen_continuous(
        self,
        callback: Callable[[str], bool],
        wake_word: Optional[str] = None,
    ):
        """Continuously listen and call callback."""
        self._init_model()
        self._is_listening = True
        
        console.print("[bold green]🎤 Continuous listening started[/bold green]")
        if wake_word:
            console.print(f"[dim]Wake word: \"{wake_word}\"[/dim]")
        
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
            return True
            
        except Exception as e:
            console.print(f"[red]❌ No microphone found: {e}[/red]")
            return False
