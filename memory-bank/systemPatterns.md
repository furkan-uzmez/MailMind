# System Patterns

## Architecture
MailMind follows a modular, pluggable architecture designed for easy switching between local and cloud providers.

### Core Components
1.  **Main Entry (`src/main.py`)**: Bootstraps the application and runs the LangGraph workflow.
2.  **Workflow Engine (`src/core/graph.py`)**: **LangGraph** state machine that manages the lifecycle of email processing vs user interaction.
3.  **State Management (`src/core/state.py`)**: Typed `AgentState` managing context (Email, Summary, Conversation History).
4.  **Email Client (`src/core/email_client.py`)**: Handles IMAP/SMTP interactions.
5.  **LLM Engine (`src/core/llm/`)**: Abstracts LLM providers.
6.  **Audio Subsystem (`src/audio/`)**: STT and TTS providers.

### Design Patterns
-   **State Machine (LangGraph)**: Replaces procedural loops. Nodes represent actions (Classify, Speak, Listen), edges represent flow control.
-   **Factory Pattern**: Used for LLM, STT, and TTS providers.
-   **Strategy Pattern**: Swappable algorithms for processing.

### Data Flow
1.  **Input**: IMAP fetch -> `Email` Object.
2.  **Graph Start**: `Email` object injected into `AgentState`.
3.  **Processing Nodes**: Classify -> Security Scan -> Summarize.
4.  **Interaction Loop**:
    -   Speak Summary -> Wait for Voice Input.
    -   Router decides next step: Reply (Draft Node), Skip (End), Question (QA Node), or Repeat.

### Tech Debt / Considerations
-   **Async/Sync**: Graph nodes run synchronously currently; future optimization could parallelize scanning/classification.
-   **Recursion Limit**: Long conversations need a high recursion limit in LangGraph.
