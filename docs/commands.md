# Admin Commands Guide

Control your bot directly from Instagram DMs. Commands must be sent from the `ADMIN_USERNAME` configured in `.env`.

## Commands List

| Command | Description | Example |
| :--- | :--- | :--- |
| `!stop` | **Pause** the bot. It will stay online but stop replying to target users. Useful if you want to take over the chat manually. | `!stop` |
| `!start` | **Resume** the bot from a paused state. | `!start` |
| `!ignore <n>` | Pause the bot for **n minutes**. After the timer expires, it automatically resumes. | `!ignore 30` (Pauses for 30 mins) |
| `!kill` | **Terminate** the bot process completely. The script will exit. If simple `python bot.py` was used, it stops. If `.bat` script was used, it might restart depending on loop logic (check your bat file). | `!kill` |

## Responses
The bot will reply to the admin thread to confirm the command:
- "Bot Paused ⏸️"
- "Bot Resumed ▶️"
- "Sleeping for X mins ⏳"
