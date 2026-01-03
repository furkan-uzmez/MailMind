# Project Brief: MailMind

## Vision
MailMind is a privacy-first, local AI assistant that connects to your email, performs intelligent triage (summarize & classify), and offers a hands-free voice interface. The user can listen to summaries and "talk back" to the AI to draft replies or ask questions about their inbox.

## Core Features
1.  **Ingestion**: Fetch unread emails via IMAP securely.
2.  **Processing (The "Brain")**:
    -   **Summarizer**: Condense email body into 1-2 sentences.
    -   **Classifier**: Tag as `IMPORTANT`, `NEWSLETTER`, or `SPAM`.
3.  **Voice Interface**:
    -   **Read-out**: TTS engine reads the summaries of "Important" emails.
    -   **Interaction**: User can say "Reply to the last one" or "What did John say?", captured via Microphone -> Whisper -> LLM.
4.  **Privacy**: All processing happens locally (Ollama, Whisper). Option to use cloud providers.
5.  **UI**: Terminal-based with `rich` for pretty printing ("Vibe coding" focus).

## Primary Goals
-   Enable hands-free email management.
-   Provide a privacy-centric alternative to cloud AI assistants.
-   Create a "premium" CLI experience.
