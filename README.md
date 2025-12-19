# 🤖 Instagram Gemini AI Bot (Thai "Kwan-Teen" Persona)

A production-grade, 24/7 Instagram DM Automation Bot that acts as a sarcastic, witty Thai friend. Powered by Google Gemini AI (`gemini-3-flash` & `gemini-2.5-flash`), featuring human-like behavior, anti-bot detection, and robust admin controls.

## ✨ Features

*   **AI-Powered Responses:** Uses Google Gemini AI to generate creative, short, and "kwan-teen" (witty/sarcastic) Thai responses.
*   **Model Rotation:** Automatically rotates between `gemini-3-flash-preview` and `gemini-2.5-flash-lite` to prevent API rate limits.
*   **Human-Like Behavior:**
    *   **Thinking Delay:** Random 1-5s delay before generating a response.
    *   **Typing Simulation:** Calculates realistic typing time based on response length.
    *   **Polling Interval:** Checks for messages every 10 seconds.
*   **Smart Targeting:** Only replies to specific users defined in your configuration.
*   **Admin Commands:** Control the bot remotely via Instagram DMs.
*   **Auto-Restart:** Includes a Windows `.bat` script to automatically restart the bot if it crashes.
*   **Strict Persona:** Enforced to be short (< 1 sentence) and avoids profanity unless provoked.

## 🛠️ Prerequisites

*   **Python:** Version 3.10, 3.11, or 3.12 (Avoid 3.14+ due to compatibility issues).
*   **Instagram Account:** Determining the "Bot" account.
*   **Target Accounts:** Usernames of people you want the bot to reply to.
*   **Google Gemini API Key:** Get one for free at [Google AI Studio](https://aistudio.google.com/).

## 📥 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/champyod/instagram-bot.git
    cd instagram-bot
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/Mac:
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

1.  Create a `.env` file in the project root (copy from `.env.example`):
    ```bash
    cp .env.example .env
    ```

2.  Fill in your details in `.env`:
    ```ini
    # Instagram Credentials
    IG_USERNAME=your_bot_username
    IG_PASSWORD=your_bot_password

    # Admin Control
    ADMIN_USERNAME=your_admin_username

    # Who to reply to (Comma Separated USERNAMES)
    TARGET_USERS=friend1,friend2,crush_account

    # Google Gemini API Key
    GEMINI_API_KEY=AIz...
    ```
    *   **Note:** Use **Usernames** (handles), NOT Display Names.

## 🚀 Usage

### Manual Run
Run the bot directly to test (and perform initial 2FA login):
```bash
python bot.py
```
*   *Note:* The first run might ask for 2FA code in the terminal. Once logged in, it saves `ig_session.json` for future auto-logins.

### 24/7 Auto-Restart (Windows)
Double-click the **`run_bot.bat`** file.
*   This script will loop forever. If the bot crashes, it waits 10 seconds and restarts it automatically.

## 👮 Admin Commands

Send these commands to the bot from your configured `ADMIN_USERNAME` account via Instagram DM:

*   `!stop`: **Pause** the bot. It will stay online but stop replying to target users.
*   `!start`: **Resume** the bot from a paused state.
*   `!ignore <n>`: Pause the bot for **n minutes** (e.g., `!ignore 30`). It automatically resumes after the timer.
*   `!kill`: **Terminate** the bot process completely (exits the script).

## 📝 Logs

The bot provides detailed logs in the console:
*   **Login Status:** `✅ LOGIN SUCCESSFUL`
*   **Thread Status:** `📩 UNREAD` vs `✅ Read`
*   **Usernames:** Shows `Display Name [username]` so you can verify targets.
*   **Actions:** "Thinking...", "Typing...", "Sent response..."

## ⚠️ Troubleshooting

*   **429 Resource Exhausted:** The bot automatically rotates models, but if you still hit limits, check your Google AI Studio quota.
*   **Login Challenges:** If `instagrapi` keeps failing login, delete `ig_session.json` and run `python bot.py` manually to re-authenticate.
*   **"Model Not Found":** Ensure you are using the latest `bot.py` which uses correct model IDs (`gemini-3-flash-preview`).

---
**Disclaimer:** This tool is for educational purposes. Automating personal Instagram accounts may violate Instagram's Terms of Service. Use at your own risk.
