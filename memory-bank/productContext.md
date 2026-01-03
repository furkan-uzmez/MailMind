# Product Context

## Why this project exists
Email management is often a tedious, screen-bound activity. Users want meaningful interactions with their inbox without being glued to a screen. Existing AI assistants often sacrifice privacy by sending data to the cloud. MailMind exists to solve both problems: hands-free efficiency and local privacy.

## Problems Solved
-   **Email Overload**: Users are overwhelmed by newsletters and spam. MailMind triages this automatically.
-   **Screen Fatigue**: Allows users to "listen" to their inbox while doing other tasks (driving, cooking, etc.).
-   **Privacy Concerns**: Ensures sensitive email data stays on the local machine by default.

## User Experience
-   **Hands-Free**: The primary interaction mode is voice.
-   **Vibe Coding**: The terminal UI is designed to be visually appealing ("Cyberpunk", "Rich" output).
-   **Fast & Local**: Responses should be snappy, leveraging local compute.

## How it works (User Journey)
1.  User runs `python -m src.main`.
2.  App connects to IMAP and fetches unread emails.
3.  App displays a loading spinner/progress in the terminal.
4.  App announces "You have 5 unread emails. 2 are important."
5.  App reads the summary of the first important email.
6.  User can interrupt/skip or ask "Reply saying..."
7.  App handles the command and proceeds to the next email.
