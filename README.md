# longueuil-aweille 🏛️

[![Longueuil](https://img.shields.io/badge/Longueuil-Québec-blue)](https://longueuil.quebec)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-halfguru%2Flongueuil--aweille-black?logo=github)](https://github.com/halfguru/longueuil-aweille)

> **Aweille!** Tanné de cliquer F5 comme un fou pour inscrire tes kids aux activités municipales de Longueuil? Calmez-vous, on a la solution!

Automate municipal activity registration at Longueuil's recreation website using Playwright. No more F5 warrior life, no more missing spots because you blinked.

## Pourquoi?

Vous connaissez le drill:
- 🕐 L'inscription ouvre à minuit
- 😰 Vous êtes 47 personnes sur la même page
- 💀 La classe est complète en 30 secondes
- 🤬 Vous restez sur une erreur 500

**Aweille!** Laissez le bot faire le travail pendant vous prenez un bon café (ou une bière, on juge pas).

## Features

- 🎯 Auto-register for any municipal activity (swimming, art, sports, whatever)
- 👥 Support for multiple participants
- 🔄 Auto-retry when registration isn't open yet
- 📝 Simple TOML configuration
- 🖥️ CLI with rich output
- 🇶🇦 Optional Quebec French vibes

## Installation

```bash
# Using uv (recommended, like everything in 2025)
uv sync

# Using pip (old school)
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

[[participants]]
name = "Votre Enfant"
dossier = "01234567890123"
nip = "5145551234"
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `headless` | Run browser without visible window | `false` |
| `timeout` | Maximum wait time in seconds | `600` |
| `refresh_interval` | Seconds between page refreshes | `5.0` |
| `domain` | Activity domain/category | Required |
| `activity_name` | Activity name to search for | Required |
| `participants` | List of participants to register | Required |

### Finding Your Domain and Activity

1. Visit the [Longueuil registration site](https://loisir.longueuil.quebec/inscription/)
2. Click "Domaines" tab to see available domains
3. Search and note the exact activity name you want

## Usage

### Basic Usage

```bash
# Run with config.toml
aweille

# Or with uv
uv run aweille
```

### CLI Options

```bash
# Show help
aweille --help

# Run in headless mode (background)
aweille --headless

# Custom timeout
aweille --timeout 300

# Custom config file
aweille --config my-config.toml
```

### Programmatic Usage

```python
import asyncio
from longueuil_aweille import Settings, RegistrationBot

async def main():
    settings = Settings.from_toml("config.toml")
    bot = RegistrationBot(settings)
    status = await bot.run()
    print("Yé!" if status == "success" else "Ah shit")

asyncio.run(main())
```

## How It Works

1. Opens the Longueuil recreation website
2. Selects your domain (activity category)
3. Searches for the activity by name across all pages
4. Waits for registration to open (refreshing periodically like you would manually)
5. Snatches the spot when it becomes available
6. Fills in dossier and NIP credentials
7. Submits the registration
8. Profit 🎉

## Status Messages

The bot will tell you what happened:
- ✅ `Yé! Registration completed!` - Spot secured, félicitations!
- ⚠️ `Already enrolled` - You're already in, calmez-vous
- ❌ `Invalid credentials` - Check your dossier/NIP, something's wrong
- ⏱️ `Timed out` - Registration never opened, try again next season

## Disclaimer

This tool is for personal use to automate a tedious manual process that everyone does anyway. Use responsibly and in accordance with the website's terms of service.

On est pas responsables si:
- Le site change
- Ça bug
- Vous vous faites bannir (unlikely mais bon)
- Votre enfant décide finalement qu'il aime pas la natation

## License

MIT - Faites-en bon usage, tabarnak!
