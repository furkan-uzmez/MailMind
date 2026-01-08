# Active Context

## Current Focus
Initial Memory Bank setup. The project structure and core documentation are being analyzed to populate the Memory Bank for the first time.

## Recent Changes
-   **LangGraph Integration**: Refactored `src/main.py` to use a stateful graph workflow (`src/core/graph.py`, `src/core/state.py`) instead of procedural loops.
-   **Dependencies**: Added `langgraph` to `requirements.txt`.
-   **Memory Bank**: Initialized and updated architecture docs.

## Active Decisions
-   **Orchestration**: Switched to **LangGraph** to handle complex conversation flows (e.g., repeating, answering questions, drafting replies) more significantly.
-   **Security**: Integrated link scanning into the graph flow before summarization.

## Next Steps
-   Complete `progress.md`.
-   Verify all Memory Bank files are present.
-   Wait for user instructions on specific development tasks (e.g., implementing specific phases from the roadmap).
