# 🧠 MailMind

**Privacy-First Local AI Email Assistant**

A hands-free email assistant that uses local AI to intelligently triage your inbox. All processing happens on your machine - no data sent to cloud APIs.

## ⚡ Features

- 📬 **Smart Email Triage**: Automatically classifies emails as Important, Newsletter, or Spam
- 📝 **AI Summarization**: Condenses emails into 1-2 sentence summaries
- 🔊 **Voice Interface**: TTS reads important emails, STT captures voice commands
- 🔒 **100% Local**: Uses Ollama for LLM, faster-whisper for STT, edge-tts for TTS
- 🎨 **Cyberpunk Terminal UI**: Beautiful rich console output

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Ollama (Llama 3.2 / Mistral) |
| STT | faster-whisper (int8 quantized) |
| TTS | edge-tts + pyttsx3 fallback |
| Email | IMAP/SMTP |
| UI | rich terminal library |

## 📦 Installation

### Prerequisites

1. **Python 3.11+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)
3. **Audio dependencies** (Linux):
   ```bash
   sudo apt install portaudio19-dev mpv
   ```

### Setup

```bash
# Clone and enter directory
cd MailMind

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your email credentials
```

### Pull Ollama Model

```bash
# Start Ollama server
ollama serve &

# Pull a model (choose one)
ollama pull llama3.2     # Recommended
ollama pull mistral      # Alternative
```

## ⚙️ Configuration

Edit `.env` with your settings:

```env
# Email Credentials (REQUIRED)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# IMAP Server (Gmail default)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Ollama
OLLAMA_MODEL=llama3.2

# Audio (optional)
WHISPER_MODEL=base
TTS_VOICE=en-US-AriaNeural
```

### Gmail Setup

1. Enable 2-Factor Authentication
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the 16-character app password as `EMAIL_PASS`

## 🚀 Usage

### Basic (Single Check)

```bash
python -m src.main
```

### Continuous Mode

```bash
python -m src.main --continuous --interval 60
```

### Text-Only (No Voice)

```bash
python -m src.main --no-voice
```

### Quick Test (LLM Only)

```bash
python -m src.core.llm_engine
```

## 🎤 Voice Commands

After an important email is read aloud:

| Say This | What Happens |
|----------|--------------|
| "Reply" | Prompts for reply content, drafts with AI |
| "Skip" / "Next" | Move to next email |
| "Read again" | Repeats the summary |
| Any question | AI answers based on email context |

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test LLM classification
pytest tests/test_llm.py -v

# Quick LLM test (requires Ollama)
python -m src.core.llm_engine
```

## 📂 Project Structure

```
MailMind/
├── src/
│   ├── main.py              # Event loop & UI
│   ├── config.py            # Settings from .env
│   ├── core/
│   │   ├── email_client.py  # IMAP connection
│   │   └── llm_engine.py    # Ollama wrapper
│   └── audio/
│       ├── speaker.py       # TTS (edge-tts)
│       └── listener.py      # STT (whisper)
├── tests/
│   ├── dummy_emails.json    # Test fixtures
│   └── test_llm.py          # LLM tests
├── .env.example
├── requirements.txt
└── README.md
```

## 🔮 Roadmap

- [x] Phase 1: Email fetching via IMAP
- [x] Phase 2: LLM classification & summarization
- [x] Phase 3: TTS voice output
- [x] Phase 4: STT voice commands
- [ ] Phase 5: Email reply sending via SMTP
- [ ] Phase 6: Calendar integration
- [ ] Phase 7: Custom voice wake word

## 📄 License

MIT License - Use freely, keep it local, stay private.

---

<p align="center">
  <em>🔒 Your emails stay on your machine. Always.</em>
</p>
