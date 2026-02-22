# Longueuil Registration

Automate swimming class registration at Longueuil's recreation website using Playwright.

## Features

- 🏊 Automatic registration for swimming classes
- 📋 Support for multiple family members
- ⚙️ Configurable via TOML or environment variables
- 🖥️ CLI with rich output
- 🔄 Automatic retry with configurable intervals

## Installation

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -e .
```

Install Playwright browsers:

```bash
playwright install chromium
```

## Configuration

### Option 1: TOML Config File (Recommended)

Create a `config.toml` based on the example:

```bash
cp config.example.toml config.toml
```

Edit `config.toml` with your details:

```toml
headless = false
timeout = 600
refresh_interval = 5.0

[[family_members]]
name = "Your Child"
dossier = "01234567890123"
nip = "5145551234"
```

### Option 2: Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

## Usage

### Basic Usage

```bash
# Using config.toml
longueuil register

# Or with uv
uv run longueuil register
```

### CLI Options

```bash
# Show help
longueuil --help

# Run in headless mode
longueuil register --headless

# Custom timeout
longueuil register --timeout 300

# Custom config file
longueuil register --config my-config.toml
```

### Programmatic Usage

```python
import asyncio
from longueuil_registration import Settings, RegistrationBot

async def main():
    settings = Settings(
        headless=False,
        family_members=[
            {"name": "Child", "dossier": "01234567890123", "nip": "5145551234"}
        ]
    )
    bot = RegistrationBot(settings)
    success = await bot.run()
    print("Success!" if success else "Failed")

asyncio.run(main())
```

## Development

### Setup

```bash
uv sync --dev
```

### Commands

```bash
# Run tests
pytest

# Run a single test
pytest tests/test_config.py::test_family_member

# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy src
```

## How It Works

1. Opens the Longueuil recreation registration website
2. Selects the specified activity category
3. Waits for registration to open (refreshing periodically)
4. Selects activities for each family member
5. Fills in dossier and NIP credentials
6. Submits the registration

## Disclaimer

This tool is for personal use to automate a tedious manual process. Use responsibly and in accordance with the website's terms of service.

## License

MIT
