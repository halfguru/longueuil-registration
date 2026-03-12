# longueuil-aweille

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Automate municipal activity registration for the City of Longueuil recreation website. Avoid manual page refreshing and never miss a spot again.

> **Aweille!** — "Hurry up!" in Quebec French. Because spots vanish in seconds.

## Features

- Auto-register for any municipal activity (swimming, art, sports, etc.)
- Credential verification before registration
- Multiple participant support
- Auto-retry when registration is not yet open
- Simple TOML configuration
- CLI with rich output

## Installation

```bash
uv sync
uv run playwright install chromium
```

## Configuration

Create a `config.toml` file:

```toml
headless = false
timeout = 600
refresh_interval = 5.0
domain = "Activités aquatiques (Vieux-Longueuil)"
activity_name = "Parent-bébé"

[[participants]]
name = "Votre Enfant"
carte_acces = "01234567890123"
telephone = "5145551234"
age = 5
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `headless` | Run browser without visible window | `false` |
| `timeout` | Maximum wait time in seconds | `600` |
| `refresh_interval` | Seconds between page refreshes | `5.0` |
| `domain` | Activity domain/category | Required |
| `activity_name` | Activity name to search for | Required |
| `participants` | List of participants | Required |

### Participant Options

| Option | Description |
|--------|-------------|
| `name` | Participant name for logging |
| `carte_acces` | Numéro de carte d'accès (14 digits) |
| `telephone` | Numéro de téléphone (10 digits) |
| `age` | Participant age for validation |

### Finding Your Domain and Activity

1. Visit the [Longueuil registration site](https://loisir.longueuil.quebec/inscription/)
2. Click "Domaines" to see available categories
3. Note the exact activity name you want

## Usage

```bash
# Run registration (verifies credentials by default)
uv run aweille register

# Skip credential verification
uv run aweille register --no-verify

# Run in headless mode
uv run aweille register --headless

# Custom timeout and config
uv run aweille register --timeout 300 --config my-config.toml

# Verify credentials separately
uv run aweille verify --carte 01234567890123 --tel 5145551234

# Browse available activities
uv run aweille browse

# Browse with filters
uv run aweille browse --domain "Activités aquatiques" --available --age 5

# Browse by day and location
uv run aweille browse --day samedi --location "Vieux-Longueuil"
```

### Programmatic Usage

```python
import asyncio
from longueuil_aweille import Settings, RegistrationBot
from longueuil_aweille.registration import RegistrationStatus

async def main():
    settings = Settings.from_toml("config.toml")
    bot = RegistrationBot(settings)
    status = await bot.run()
    
    if status == RegistrationStatus.SUCCESS:
        print("Registration completed")
    else:
        print(f"Registration failed: {status.value}")

asyncio.run(main())
```

## How It Works

1. Opens the Longueuil recreation website
2. Selects the configured domain (activity category)
3. Searches for the activity by name across all pages
4. Waits for registration to open (refreshes periodically)
5. Registers when the spot becomes available
6. Fills in participant credentials
7. Submits the registration

## Status Codes

| Status | Description |
|--------|-------------|
| `SUCCESS` | Registration completed successfully |
| `ALREADY_ENROLLED` | Participant already registered |
| `INVALID_CREDENTIALS` | Carte d'accès or téléphone incorrect |
| `AGE_CRITERIA_NOT_MET` | Participant outside age range |
| `ACTIVITY_FULL` | No spots available |
| `ACTIVITY_CANCELLED` | Activity was cancelled |
| `REGISTRATION_NEVER_AVAILABLE` | Online registration not offered |
| `TIMEOUT` | Registration never opened within timeout |
| `FAILED` | Unexpected error |

## Disclaimer

This tool is for personal use to automate a tedious manual process. Use responsibly and in accordance with the website's terms of service.

## License

MIT
