# Instagram DM Bot Walkthrough

This guide explains how to set up and run your 24/7 Instagram automation bot.

## Prerequisites
- Python installed on your Windows machine (Recommended: Python 3.10 - 3.12).
  > [!WARNING]
  > avoid Python 3.14+ as some libraries (like `instagrapi`) might not support it yet.
- A Google Cloud Project with Gemini API enabled (API Key).
- An Instagram account (credentials).

## Setup Instructions

1.  **Install Dependencies**
    Open Command Prompt in the project folder and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment**
    - Rename `.env.example` to `.env`.
    - Open `.env` and fill in your details:
        - `IG_USERNAME` / `IG_PASSWORD`: Your bot's account.
        - `ADMIN_USERNAME`: Your personal account (to use the `!stop` command).
        - `TARGET_USERS`: Comma-separated list of usernames to reply to (e.g., `friend1,friend2`).
        - `GEMINI_API_KEY`: Your API key from Google AI Studio.

## Running the Bot

### First Run (Important!)
Run the bot manually the first time to handle 2FA and save the session:
```bash
python bot.py
```
*If prompted for a 2FA code, enter it in the console.*

### Automatic Run (24/7)
Double-click `run_bot.bat`.
- This will start the bot.
- If the bot crashes or requests specific errors, it will automatically restart after 10 seconds.

### TUI Mode (New!)
Run with `-t` flag for a visual dashboard:
```bash
python bot.py -t
```

## Features Verification
- **Session Management**: Check for `ig_session.json` after the first login.
- **Anti-Bot**: Watch the console for "Thinking..." and "Typing..." logs with random delays.
- **Kill Switch**: Send `!stop` from your Admin account to the bot in DMs. The console should show "Kill switch activated" and the script will pause.

## Troubleshooting
- **Login Issues**: If you get "Suspicious Login", try logging in to the account on the browser on the same PC first, or wait a few hours.
- **2FA**: If `instagrapi` cannot handle your 2FA method, disable 2FA temporarily to generate the session file, then re-enable it (though re-enabling might invalidate the session).
