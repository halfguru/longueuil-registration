import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import Settings
from .registration import RegistrationBot, RegistrationStatus

app = typer.Typer(
    name="longueuil-aweille",
    help="Aweille! Auto-register for Longueuil municipal activities before anyone else",
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"longueuil-aweille version {__version__}")
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
    _ = version
    """Run the registration bot. Aweille!"""
    console.print()
    console.print(f"[dim]Loading config from {config}[/dim]")
    settings = Settings.from_toml(config)

    if headless is not None:
        settings.headless = headless
    if timeout is not None:
        settings.timeout = timeout

    if not settings.participants:
        console.print("[red]Error: No participants configured[/red]")
        raise typer.Exit(1)

    # Display activity info in a nice panel
    console.print()
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_row("[bold]Domain:[/]", settings.domain)
    info_table.add_row("[bold]Activity:[/]", settings.activity_name)
    info_table.add_row("[bold]Participants:[/]", str(len(settings.participants)))

    console.print(
        Panel(
            info_table,
            title="[bold cyan]🎯 Target Activity[/]",
            border_style="cyan",
        )
    )

    # Display participants
    for participant in settings.participants:
        console.print(f"  [green]•[/] {participant.name}")

    console.print()

    bot = RegistrationBot(settings)
    status = asyncio.run(bot.run())

    console.print()

    match status:
        case RegistrationStatus.SUCCESS:
            console.print(
                Panel("[green bold]🎉 Yé! Registration completed![/]", border_style="green")
            )
        case RegistrationStatus.ALREADY_ENROLLED:
            console.print(
                Panel(
                    "[yellow]Already enrolled in this activity, câlisse[/]", border_style="yellow"
                )
            )
        case RegistrationStatus.INVALID_CREDENTIALS:
            console.print(
                Panel(
                    "[bold red]❌ Invalid credentials - check dossier and NIP[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        case RegistrationStatus.TIMEOUT:
            console.print(Panel("[bold red]⏱️ Registration timed out[/]", border_style="red"))
            raise typer.Exit(1)
        case _:
            console.print(Panel("[bold red]💥 Ah shit, registration failed[/]", border_style="red"))


if __name__ == "__main__":
    app()
