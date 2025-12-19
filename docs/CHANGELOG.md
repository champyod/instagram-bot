# Changelog

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
