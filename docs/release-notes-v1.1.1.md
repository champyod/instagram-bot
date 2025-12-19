# Release v1.1.1

## 🔄 Target Synchronization
- **.env Source of Truth**: On every startup, the bot now ensures that users listed in `.env` are present in the target list.
- **Smart Merging**: Automatically merges targets from `.env` with any new targets added dynamically via `!add` (stored in `targets.json`).
- **Persistence**: Runtime additions are preserved, but `.env` configuration is never lost.

## 📝 Documentation
- Updated `README.md` to clarify the new target loading behavior.
