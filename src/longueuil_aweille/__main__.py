import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .browse import ActivityScraper, DomainNotFoundError
from .config import Settings
from .registration import RegistrationBot
from .status import ActivityStatus, RegistrationStatus
from .verify import VerificationBot, VerificationStatus

app = typer.Typer(
    name="longueuil-aweille",
    help="Auto-register for Longueuil municipal activities",
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"longueuil-aweille version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
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
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@app.command()
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
    verify_credentials: bool = typer.Option(
        True,
        "--verify/--no-verify",
        help="Verify credentials before registration",
    ),
) -> None:
    """Run the registration bot."""
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

    if verify_credentials:
        console.print("[dim]Verifying credentials...[/dim]")
        for participant in settings.participants:
            bot = VerificationBot(
                carte_acces=participant.carte_acces,
                telephone=participant.telephone,
                headless=True,
            )
            status = asyncio.run(bot.run())
            if status == VerificationStatus.INVALID:
                console.print(f"[red]Invalid credentials for {participant.name}[/red]")
                raise typer.Exit(1)
            elif status == VerificationStatus.ERROR:
                console.print(
                    f"[yellow]Could not verify {participant.name}, continuing anyway[/yellow]"
                )
            else:
                console.print(f"[green]Verified {participant.name}[/green]")
        console.print()

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_row("[bold]Domain:[/]", settings.domain)
    info_table.add_row("[bold]Activity:[/]", settings.activity_name)
    info_table.add_row("[bold]Participants:[/]", str(len(settings.participants)))

    console.print(
        Panel(
            info_table,
            title="[bold]Target Activity[/]",
            border_style="cyan",
        )
    )

    for participant in settings.participants:
        console.print(f"  {participant.name}")

    console.print()

    reg_bot = RegistrationBot(settings)
    reg_status = asyncio.run(reg_bot.run())

    console.print()

    match reg_status:
        case RegistrationStatus.SUCCESS:
            console.print(Panel("[green bold]Registration completed[/]", border_style="green"))
        case RegistrationStatus.ALREADY_ENROLLED:
            console.print(
                Panel("[yellow]Already enrolled in this activity[/]", border_style="yellow")
            )
        case RegistrationStatus.INVALID_CREDENTIALS:
            console.print(
                Panel(
                    "[bold red]Invalid credentials - check carte acces and telephone[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        case RegistrationStatus.AGE_CRITERIA_NOT_MET:
            console.print(
                Panel(
                    "[bold red]Age criteria not met for this activity[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        case RegistrationStatus.ACTIVITY_FULL:
            console.print(
                Panel(
                    "[bold red]Activity is full - no spots available[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        case RegistrationStatus.ACTIVITY_CANCELLED:
            console.print(
                Panel(
                    "[bold red]Activity is cancelled[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        case RegistrationStatus.REGISTRATION_NEVER_AVAILABLE:
            console.print(
                Panel(
                    "[bold red]Online registration not available for this activity[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        case RegistrationStatus.TIMEOUT:
            console.print(Panel("[bold red]Registration timed out[/]", border_style="red"))
            raise typer.Exit(1)
        case _:
            console.print(Panel("[bold red]Registration failed[/]", border_style="red"))


@app.command()
def verify(
    carte_acces: str = typer.Option(..., "--carte", "-c", help="Numéro de carte d'accès"),
    telephone: str = typer.Option(..., "--tel", "-t", help="Numéro de téléphone"),
    headless: bool = typer.Option(True, help="Run browser in headless mode"),
) -> None:
    """Verify account credentials are valid."""
    console.print()
    console.print(f"[dim]Verifying credentials for carte: {carte_acces}[/dim]")

    bot = VerificationBot(carte_acces=carte_acces, telephone=telephone, headless=headless)
    status = asyncio.run(bot.run())

    console.print()

    match status:
        case VerificationStatus.VALID:
            console.print(Panel("[green bold]Credentials valid[/]", border_style="green"))
        case VerificationStatus.INVALID:
            console.print(Panel("[bold red]Credentials invalid[/]", border_style="red"))
            raise typer.Exit(1)
        case VerificationStatus.ERROR:
            console.print(Panel("[bold red]Verification failed[/]", border_style="red"))
            raise typer.Exit(1)


@app.command()
def browse(
    domain: str = typer.Option(
        "",
        "--domain",
        "-d",
        help="Domain to filter (e.g., 'Activités aquatiques')",
    ),
    available_only: bool = typer.Option(
        False,
        "--available",
        "-a",
        help="Show only activities with available spots",
    ),
    name_contains: str = typer.Option(
        "",
        "--name",
        "-n",
        help="Filter by activity name",
    ),
    location_contains: str = typer.Option(
        "",
        "--location",
        "-l",
        help="Filter by location",
    ),
    day: str = typer.Option(
        "",
        "--day",
        help="Filter by day of week (e.g., 'mon', 'tue', 'samedi')",
    ),
    age: int = typer.Option(
        0,
        "--age",
        help="Filter by age (e.g., 5, 8, 12)",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--no-headless",
        help="Run browser in headless mode",
    ),
) -> None:
    """Browse available activities."""
    console.print()

    filters = []
    if domain:
        filters.append(f"domain: {domain}")
    if available_only:
        filters.append("available only")
    if name_contains:
        filters.append(f"name: {name_contains}")
    if location_contains:
        filters.append(f"location: {location_contains}")
    if day:
        filters.append(f"day: {day}")
    if age:
        filters.append(f"age: {age}")

    if filters:
        console.print(f"[dim]Browsing activities ({', '.join(filters)})[/dim]")
    else:
        console.print("[dim]Browsing all activities[/dim]")

    scraper = ActivityScraper(
        domain=domain,
        available_only=available_only,
        headless=headless,
    )

    try:
        activities = asyncio.run(scraper.run())
    except DomainNotFoundError as e:
        console.print(f"[bold red]Error: Domain '{e.domain}' not found[/bold red]")
        if e.available_domains:
            console.print("\n[yellow]Available domains:[/yellow]")
            for d in e.available_domains:
                console.print(f"  • {d}")
        raise typer.Exit(1) from None

    if name_contains or location_contains or day or age:
        activities = scraper.filter_activities(
            name_contains=name_contains,
            location_contains=location_contains,
            day=day,
            age=age,
        )

    if not activities:
        console.print("[yellow]No activities found matching criteria[/yellow]")
        return

    table = Table(title=f"Activities ({len(activities)} found)")
    table.add_column("Activity", style="cyan", no_wrap=False, width=35)
    table.add_column("Age", style="white", width=10)
    table.add_column("Day/Time", style="white", width=20)
    table.add_column("Location", style="white", width=25)
    table.add_column("Spots", style="white", justify="right", width=6)
    table.add_column("Reg. Opens", style="white", width=18)
    table.add_column("Status", style="white", width=12)

    status_styles = {
        ActivityStatus.AVAILABLE: "[green]Available[/]",
        ActivityStatus.FULL: "[red]Full[/]",
        ActivityStatus.CANCELLED: "[red]Cancelled[/]",
        ActivityStatus.NEVER_AVAILABLE: "[dim]Never[/]",
        ActivityStatus.NOT_YET: "[yellow]Not yet[/]",
    }

    for activity in activities:
        status_str = status_styles.get(activity.status, activity.status.value)
        age_str = (
            f"{activity.age_min}-{activity.age_max}"
            if activity.age_max < 150
            else f"{activity.age_min}+"
        )
        schedule = f"{activity.days[:10]} {activity.times[:8]}".strip()
        location = activity.location[:25] if activity.location else "-"

        reg_opens = "-"
        if activity.registration_dates and activity.registration_dates.resident_start:
            date_str = activity.registration_dates.resident_start
            if "," in date_str:
                date_str = date_str.split(",")[0]
            reg_opens = date_str[:16]

        table.add_row(
            activity.name[:35],
            age_str,
            schedule[:20],
            location,
            str(activity.spots),
            reg_opens,
            status_str,
        )

    console.print()
    console.print(table)


if __name__ == "__main__":
    app()
