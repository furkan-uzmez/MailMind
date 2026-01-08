# 🧠 MailMind

**Privacy-First Local AI Email Assistant**

A hands-free email assistant that uses local AI to intelligently triage your inbox. Supports both local (default) and cloud providers.

## ⚡ Features

- 📬 **Smart Email Triage**: Automatically classifies emails as Important, Newsletter, or Spam
- 📝 **AI Summarization**: Condenses emails into 1-2 sentence summaries
- 🔊 **Voice Interface**: TTS reads all email summaries aloud
- ⏭️ **Skip Playback**: Press Enter during TTS to skip current email
- 📊 **Usage Statistics**: Tracks sessions and emails processed
- 🕸️ **Agentic Workflow**: Powered by **LangGraph** for stateful, robust conversations
- 🔒 **Local-First**: Uses Ollama, faster-whisper, edge-tts by default
- ☁️ **Cloud-Ready**: Easily switch to OpenAI, ElevenLabs via env vars
- 🎨 **Cyberpunk Terminal UI**: Beautiful rich console output

## 🔄 Provider Architecture

MailMind uses a **pluggable provider pattern** orchestrated by a **LangGraph** state machine. Switch services via `.env`:

| Component | Local (Default) | Cloud Options |
|-----------|-----------------|---------------|
| **LLM** | Ollama | OpenAI GPT, Google Gemini |
| **STT** | faster-whisper | OpenAI Whisper API |
| **TTS** | edge-tts | ElevenLabs |

```env
# Switch to cloud providers
LLM_PROVIDER=gemini      # or "openai", "ollama" (default)
STT_PROVIDER=openai_whisper  # or "whisper" (default)
TTS_PROVIDER=elevenlabs  # or "edge" (default)
```

## 📦 Installation

### Prerequisites

1. **Python 3.11+**
2. **Ollama** (for local LLM) - Install from [ollama.ai](https://ollama.ai)
3. **Audio dependencies**:
   
   **Ubuntu/Debian**:
   ```bash
   sudo apt install portaudio19-dev mpv
   ```

   **Fedora**:
   ```bash
   sudo dnf install portaudio-devel mpv
   ```

   **Arch Linux**:
   ```bash
   sudo pacman -S portaudio mpv
   ```

   **macOS**:
   ```bash
   brew install portaudio mpv
   ```

   **Windows**:
   ```powershell
   winget install mpv.mpv
   # PortAudio is usually auto-installed with Python packages
   ```

### Setup

```bash
cd MailMind

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For cloud providers (optional)
pip install openai google-generativeai elevenlabs

# Configure environment
cp .env.example .env
nano .env
```

### Pull Ollama Model

```bash
ollama serve &
ollama pull llama3.2
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Email Credentials (REQUIRED)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
IMAP_SERVER=imap.gmail.com

# Provider Selection
LLM_PROVIDER=ollama       # ollama | openai | gemini
STT_PROVIDER=whisper      # whisper | openai_whisper
TTS_PROVIDER=edge         # edge | elevenlabs

# Local Provider Settings
OLLAMA_MODEL=llama3.2
WHISPER_MODEL=base
TTS_VOICE=en-US-AriaNeural

# Cloud Provider Keys (if using cloud)
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=...
# ELEVENLABS_API_KEY=...
```

### Parameters File (`src/parameters.py`)

Customize application behavior:

```python
# Maximum emails to fetch per run
EMAIL_COUNT = 10

# Characters shown in email preview
BODY_PREVIEW_LENGTH = 500

# Characters sent to LLM
LLM_BODY_LIMIT = 1500
```

## 🚀 Usage

```bash
# Basic run
python -m src.main

# Continuous mode
python -m src.main --continuous --interval 60

# Text-only (no voice)
python -m src.main --no-voice
```

### Skip During Playback

While TTS is speaking, you can skip to the next email:
- Press **Enter**
- Type **skip** or **s** and press Enter

## 🎤 Voice Commands

| Say This | Action |
|----------|--------|
| "Reply" | Draft reply with AI |
| "Skip" | Next email |
| "Read again" | Repeat summary |
| Any question | Ask about the email |

## 📊 Usage Statistics

MailMind tracks your usage automatically:

- **Total Sessions**: How many times you've run the app
- **Total Emails Processed**: Emails analyzed by the LLM
- **Last Session Date**: When you last used the app

Stats are saved to `mailmind_stats.json` and displayed at session end.

## 📂 Project Structure

```
MailMind/
├── src/
│   ├── main.py           # Main application
│   ├── config.py         # Environment config
│   ├── parameters.py     # App parameters
│   ├── stats.py          # Usage tracking
│   ├── core/
│   │   ├── email_client.py
│   │   └── llm/          # LLM providers
│   │       ├── base.py
│   │       ├── ollama.py
│   │       ├── openai.py
│   │       └── factory.py
│   └── audio/
│       ├── tts/          # TTS providers
│       │   ├── base.py
│       │   ├── edge.py
│       │   ├── elevenlabs.py
│       │   └── factory.py
│       └── stt/          # STT providers
│           ├── base.py
│           ├── whisper.py
│           ├── openai_whisper.py
│           └── factory.py
├── tests/
├── .env.example
├── mailmind_stats.json   # Usage statistics
└── requirements.txt
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📄 License

MIT License

---

<p align="center">
  <em>🔒 Your emails stay on your machine. Always.*</em><br>
  <small>*Unless you choose cloud providers</small>
</p>
