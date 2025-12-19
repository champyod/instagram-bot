# Changelog

## v1.1.0 (2025-12-19)

### ✨ New Features
- **Dynamic Targets**: Add/remove target users on the fly via DMs.
  - `!add <username>`
  - `!remove <username>`
  - targets are saved to `targets.json`.
- **Persona Modes**: Switch between AI personalities!
  - `!polite` / `-p`: Formal, kind Thai assistant.
  - `!joke` / `-j`: Friendly, non-insulting jokester (matches user language/Thai).
  - `!normal`: Back to the classic "kwan-teen" mode.
- **Smart Ignore**: `!ignore <username> <minutes>` to pause replies for specific users.

### 💄 CLI & TUI Improvements
- **Responsive Layout**: TUI now automatically adjusts table rows and footer height to fit your terminal window.
- **Mode Indicators**: Header displays current persona icon (😈/😇/🤡).

### 🐛 Bug Fixes
- **Language Consistency**: AI now strictly follows the user's language (defaulting to Thai), avoiding random English replies in Joke mode.

## v1.0.0 (2025-12-19)

### 🚀 Features
- **AI Integration**: Powered by Google Gemini with automatic model rotation (`gemini-3-flash-preview` & `gemini-2.5-flash-lite`) to handle rate limits.
- **Admin Commands**: Control the bot via Instagram DMs:
  - `!stop`: Pause the bot.
  - `!start`: Resume operations.
  - `!ignore <n>`: Pause for `n` minutes.
  - `!kill`: Remote kill switch.
- **TUI Mode**: New Terminal User Interface with a live dashboard (`python bot.py -t`).
- **Anti-Bot Logic**: Human-like typing delays and random polling intervals.
- **Smart Targeting**: Configurable allowlist for target users.

### 📝 Documentation
- Added `docs/walkthrough.md`.
- Added `docs/commands.md`.
