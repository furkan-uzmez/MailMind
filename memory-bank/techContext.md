# Tech Context

## Technology Stack
-   **Language**: Python 3.11+
-   **Project Structure**: Modular `src/` directory with `core/` and `audio/` packages.

## Dependencies
### Core
-   `python-dotenv`: Environment variable management.
-   `rich`: Terminal UI styling.
-   `pydantic`: Data validation and settings.

### Email
-   `beautifulsoup4`, `lxml`: HTML email parsing.
-   `requests`: HTTP requests.

### AI / Data
-   `ollama`: Local LLM interface.
-   `google-generativeai`: Cloud LLM option.
-   `openai`: Cloud LLM option (optional).

### Audio
-   **STT**: `faster-whisper` (local), `sounddevice`, `numpy`, `scipy`.
-   **TTS**: `edge-tts` (online but free), `pyttsx3` (offline fallback), `elevenlabs` (cloud premium).

### Testing
-   `pytest`: Test runner.

## Development Setup
-   **Virtual Env**: Standard `venv` recommended.
-   **Config**: `.env` file for secrets (API keys, credentials) and provider selection.
-   **Local Services**: Requires running Ollama service (`ollama serve`).

## Constraints
-   **Hardware**: Local LLM and Whisper require decent RAM/GPU/CPU resources.
-   **OS**: Cross-platform (Linux, Windows, macOS), but audio dependencies (PortAudio) vary by OS.
