# AGENTS.md - Coding Agent Guidelines

This document provides guidelines for AI coding agents working in this repository.

## Project Overview

Python automation tool for swimming class registration at Longueuil's recreation website. Uses Playwright for browser automation with a clean CLI interface.

## Build/Lint/Test Commands

### Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Install dev dependencies
uv sync --dev

# Install Playwright browsers
playwright install chromium

# Install using pip
pip install -e ".[dev]"
```

### Running the Application
```bash
# Run via CLI
longueuil register

# Run with uv
uv run longueuil register

# Run with options
uv run longueuil register --headless --timeout 300

# Run with custom config
uv run longueuil register --config my-config.toml
```

### Linting and Formatting
```bash
# Format code with ruff
ruff format .

# Lint with ruff
ruff check .

# Lint and auto-fix
ruff check . --fix

# Type checking
mypy src
```

### Testing
```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_config.py

# Run a single test function
pytest tests/test_config.py::test_family_member_creation

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=.
```

## Code Style Guidelines

### Project Structure
```
src/longueuil_registration/
├── __init__.py       # Package init, version
├── __main__.py       # CLI entry point
├── cli.py            # Typer app export
├── config.py         # Pydantic settings
└── registration.py   # Bot implementation

tests/
├── __init__.py
└── test_config.py    # Config tests
```

### Imports
```python
# Standard library first
import asyncio
import logging
from pathlib import Path

# Third-party second
from playwright.async_api import async_playwright
from pydantic import Field
from pydantic_settings import BaseSettings

# Local imports last
from .config import Settings
```

### Type Hints
Always use type hints. Use modern Python syntax:
```python
list[FamilyMember]  # Not List[FamilyMember]
dict[str, int]      # Not Dict[str, int]
str | None          # Not Optional[str]
```

### Naming Conventions
- **Modules**: snake_case (`registration.py`, `config.py`)
- **Classes**: PascalCase (`RegistrationBot`, `FamilyMember`)
- **Functions/Methods**: snake_case (`wait_for_availability`, `fill_credentials`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_SELECTORS`, `TIMEOUT`)
- **Private methods**: prefix underscore (`_navigate_and_search`)

### Configuration
Use pydantic-settings for all configuration:
- Support both TOML config files and environment variables
- Family members as list of nested models
- All settings have sensible defaults

### Error Handling
- Use specific exception types when possible
- Log errors with descriptive messages
- Return bool for success/failure in async methods

### Logging
Use Python's logging module:
```python
logger = logging.getLogger(__name__)
logger.info("Starting registration...")
logger.error(f"Failed: {e}")
```

### Comments
- No inline comments explaining obvious code
- Docstrings for public functions/classes
- Comments explain "why", not "what"

### Web Automation Best Practices
1. Use explicit waits, not arbitrary sleeps when possible
2. Small delays between actions to avoid overwhelming server
3. Always clean up browser in finally block
4. Log key actions for debugging
5. Use CSS selectors over XPaths

### Security
- Never commit `config.toml` or `.env` (in .gitignore)
- Use `config.example.toml` and `.env.example` for templates
- No hardcoded credentials in source code

## File Patterns

### Adding a new CLI command
1. Add function in `__main__.py` decorated with `@app.command()`
2. Use typer options for arguments
3. Use rich console for output

### Adding new configuration
1. Add field to `Settings` or create new pydantic model
2. Add to `config.example.toml`
3. Add to `.env.example` if applicable

## Dependencies

Core:
- `playwright` - Browser automation
- `pydantic` / `pydantic-settings` - Configuration
- `typer` - CLI framework
- `rich` - Terminal output

Dev:
- `pytest` / `pytest-asyncio` - Testing
- `ruff` - Linting and formatting
- `mypy` - Type checking
