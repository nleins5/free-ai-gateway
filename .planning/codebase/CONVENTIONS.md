# Development Conventions

## Code Style
- **Python**: PEP8-ish, but highly monolithic.
- **Naming**: `snake_case` for functions/variables.
- **Internal State**: Prefixed with `_` (e.g. `_provider_state`).
- **FastAPI**: Uses Pydantic models for request validation.

## Known Patterns
- **Global Variables**: Heavy reliance on global state for tracking (`_rr_counter`, `_daily_usage`).
- **Sync I/O**: Some synchronous file operations (`open()`) inside async routes.
- **Embedded HTML**: Large block of HTML/JS in `unified_hub()` for the debug UI.

## Gaps
- **Typing**: Some `Any` and missing type hints in complex functions.
- **Logging**: Uses basic `print` or relies on FastAPI's default logger. No structured logging.
