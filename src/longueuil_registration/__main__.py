import asyncio
from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .config import Settings
from .registration import RegistrationBot, RegistrationStatus

app = typer.Typer(
    name="longueuil-registration",
    help="Automate swimming class registration at Longueuil's recreation website",
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"longueuil-registration version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def register(
    config: Path = typer.Option(
        Path("config.toml"),
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
    headless: bool = typer.Option(
        None,
        "--headless",
        "--no-headless",
        help="Run browser in headless mode",
    ),
    timeout: int = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Timeout in seconds",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    _ = version  # Used via callback
    """Run the registration bot."""
    console.print(f"[blue]Loading config from {config}[/blue]")
    settings = Settings.from_toml(config)

    if headless is not None:
        settings.headless = headless
    if timeout is not None:
        settings.timeout = timeout

    if not settings.family_members:
        console.print("[red]Error: No family members configured[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Registering {len(settings.family_members)} family member(s)[/green]")
    for member in settings.family_members:
        console.print(f"  - {member.name}")

    bot = RegistrationBot(settings)
    status = asyncio.run(bot.run())

    if status == RegistrationStatus.SUCCESS:
        console.print("[green bold]Registration completed![/green bold]")
    elif status == RegistrationStatus.ALREADY_ENROLLED:
        console.print("[yellow]Already enrolled in this activity[/yellow]")
    elif status == RegistrationStatus.INVALID_CREDENTIALS:
        console.print("[bold red]Invalid credentials - check dossier and NIP[/]")
        raise typer.Exit(1)
    elif status == RegistrationStatus.TIMEOUT:
        console.print("[bold red]Registration timed out[/]")
        raise typer.Exit(1)
    else:
        console.print("[bold red]Registration failed[/]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
