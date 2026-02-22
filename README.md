# Longueuil Registration

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-halfguru%2Flongueuil--registration-black?logo=github)](https://github.com/halfguru/longueuil-registration)

Automate swimming class registration at Longueuil's recreation website using Playwright.

## Features

- Automatic registration for swimming classes
- Support for multiple family members
- Configurable via TOML
- CLI with rich output
- Automatic retry with configurable intervals

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

Create a `config.toml` file with your details:

```toml
headless = false
timeout = 600
refresh_interval = 5.0
domain = "Activités aquatiques (Vieux-Longueuil)"
activity_name = "Parent-bébé"

[[family_members]]
name = "Your Child"
dossier = "01234567890123"
nip = "5145551234"
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `headless` | Run browser without visible window | `false` |
| `timeout` | Maximum wait time in seconds | `600` |
| `refresh_interval` | Seconds between page refreshes | `5.0` |
| `domain` | Activity domain/category to filter | Required |
| `activity_name` | Activity name to search for | Required |
| `family_members` | List of family members to register | Required |

### Finding Your Domain and Activity

1. Visit the [Longueuil registration site](https://loisir.longueuil.quebec/inscription/)
2. Click "Domaines" tab to see available domains
3. Search and note the exact activity name you want

## Usage

### Basic Usage

```bash
# Using config.toml
longueuil

# Or with uv
uv run longueuil
```

### CLI Options

```bash
# Show help
longueuil --help

# Run in headless mode
longueuil --headless

# Custom timeout
longueuil --timeout 300

# Custom config file
longueuil --config my-config.toml
```

### Programmatic Usage

```python
import asyncio
from longueuil_registration import Settings, RegistrationBot

async def main():
    settings = Settings.from_toml("config.toml")
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
2. Selects the specified domain (activity category)
3. Searches for the activity by name across all pages
4. Waits for registration to become available (refreshing periodically)
5. Selects the activity and adds to cart
6. Fills in dossier and NIP credentials
7. Submits the registration

## Disclaimer

This tool is for personal use to automate a tedious manual process. Use responsibly and in accordance with the website's terms of service.

## License

MIT
