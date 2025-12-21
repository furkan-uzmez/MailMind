"""
Configuration management using environment variables.
Loads settings from .env file with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console

console = Console()

# Load .env file from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    console.print("[yellow]⚠️  No .env file found. Copy .env.example to .env and configure.[/yellow]")


@dataclass
class EmailConfig:
    """Email server configuration."""
    user: str = field(default_factory=lambda: os.getenv("EMAIL_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("EMAIL_PASS", ""))
    imap_server: str = field(default_factory=lambda: os.getenv("IMAP_SERVER", "imap.gmail.com"))
    imap_port: int = field(default_factory=lambda: int(os.getenv("IMAP_PORT", "993")))
    smtp_server: str = field(default_factory=lambda: os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))

    def validate(self) -> bool:
        """Check if required credentials are set."""
        if not self.user or not self.password:
            console.print("[red]❌ EMAIL_USER and EMAIL_PASS must be set in .env[/red]")
            return False
        return True


@dataclass
class OllamaConfig:
    """Ollama LLM configuration."""
    host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))


@dataclass
class AudioConfig:
    """Audio (TTS/STT) configuration."""
    whisper_model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "base"))
    whisper_device: str = field(default_factory=lambda: os.getenv("WHISPER_DEVICE", "cpu"))
    tts_voice: str = field(default_factory=lambda: os.getenv("TTS_VOICE", "en-US-AriaNeural"))


@dataclass
class Config:
    """Main configuration container."""
    email: EmailConfig = field(default_factory=EmailConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment."""
        return cls()


# Global config instance
config = Config.load()
