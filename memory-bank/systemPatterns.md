# System Patterns

## Architecture
MailMind follows a modular, pluggable architecture designed for easy switching between local and cloud providers.

### Core Components
1.  **Main Loop (`src/main.py`)**: The central event loop that orchestrates Fetch -> Process -> Speak -> Listen.
2.  **Email Client (`src/core/email_client.py`)**: Handles IMAP/SMTP interactions.
3.  **LLM Engine (`src/core/llm/`)**:
    -   Abstracts LLM providers (Ollama, OpenAI, Gemini).
    -   Handles prompt construction for classification and summarization.
4.  **Audio Subsystem (`src/audio/`)**:
    -   `stt/`: Speech-to-Text providers (Faster-Whisper, OpenAI Whisper).
    -   `tts/`: Text-to-Speech providers (Edge-TTS, ElevenLabs, pyttsx3 fallback).
5.  **Configuration (`src/config.py`, `.env`)**: Centralized config for secrets and toggles.

### Design Patterns
-   **Factory Pattern**: Used for LLM, STT, and TTS providers to allow easy instantiation based on config (e.g., `src/core/llm/factory.py`).
-   **Strategy Pattern**: Swappable algorithms for processing (Local vs Cloud).
-   **Safe Fallbacks**: If a preferred provider fails (or is not configured), the system should fail gracefully or fallback (e.g., TTS fallback).

### Data Flow
1.  **Input**: IMAP fetch -> Raw Email Data.
2.  **Processing**: Raw Data -> LLM (Summarize/Classify) -> Structured `Email` Object.
3.  **Output (Audio)**: `Email` Summary -> TTS -> Audio Output.
4.  **Input (Voice)**: Microphone -> STT -> Text Command -> LLM (Intent Parsing) -> Action (Reply/Skip/Query).

### Tech Debt / Considerations
-   **Async/Sync**: Python's async nature for I/O (IMAP) vs CPU heavy (Local LLM) needs careful management.
-   **State Management**: Tracking which emails were read/skipped within a session (likely in-memory or simple JSON stats).
