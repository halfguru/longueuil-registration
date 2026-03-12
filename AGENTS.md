# AGENTS.md - Coding Agent Guidelines

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 3. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 4. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 5. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to plan `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

See README.md for project details.

## Build/Lint/Test Commands

### Setup
```bash
# Install dependencies using uv
uv sync

# Install dev dependencies
uv sync --all-extras

# Install Playwright browsers
uv run playwright install chromium

# Configure git hooks
git config core.hooksPath .githooks
```

### Running the Application
```bash
# Run registration
uv run aweille register

# Verify credentials
uv run aweille verify --carte 01234567890123 --tel 5145551234

# Run with options
uv run aweille register --headless --timeout 300

# Run with custom config
uv run aweille register --config my-config.toml
```

### Linting and Formatting
```bash
# Format code with ruff
uv run ruff format .

# Lint with ruff
uv run ruff check .

# Lint and auto-fix
uv run ruff check . --fix

# Type checking
uv run mypy src
```

### Testing
```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_config.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=.
```
