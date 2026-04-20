import subprocess
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

console = Console()


def get_wifi_profiles():
    try:
        data = (
            subprocess.check_output(["netsh", "wlan", "show", "profiles"])
            .decode("utf-8", errors="backslashreplace")
            .split("\n")
        )
        return [i.split(":")[1][1:-1] for i in data if "All User Profile" in i]
    except subprocess.CalledProcessError:
        return []


def get_wifi_password(profile):
    try:
        results = (
            subprocess.check_output(
                ["netsh", "wlan", "show", "profile", profile, "key=clear"]
            )
            .decode("utf-8", errors="backslashreplace")
            .split("\n")
        )
        passwords = [b.split(":")[1][1:-1] for b in results if "Key Content" in b]
        return passwords[0] if passwords else None
    except subprocess.CalledProcessError:
        return "ENCODING ERROR"


def main():
    console.clear()

    # ── Header
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]📶  Wi-Fi Password Viewer[/bold cyan]\n"
            "[dim]Scanning saved profiles on this machine...[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()

    # ── Scanning profiles with spinner
    with Live(
        Spinner("dots", text=" [cyan]Scanning Wi-Fi profiles...[/cyan]"),
        refresh_per_second=10,
    ):
        profiles = get_wifi_profiles()
        time.sleep(0.8)

    if not profiles:
        console.print(
            Panel(
                "[yellow]No Wi-Fi profiles found on this device.[/yellow]",
                title="[bold yellow]Notice[/bold yellow]",
                border_style="yellow",
            )
        )
        console.print()
        console.input("[bold cyan]✅ Press Enter to close...[/bold cyan]")
        return

    console.print(
        f"[bold green]✔ Found [white]{len(profiles)}[/white] saved network(s)[/bold green]\n"
    )

    # ── Build table
    table = Table(
        title="💾  Saved Wi-Fi Networks",
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold white on dark_blue",
        show_lines=True,
        title_style="bold white",
        expand=True,
    )
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column(
        "Network Name (SSID)", justify="left", style="bold cyan", min_width=25
    )
    table.add_column("Password", justify="left", style="green", min_width=25)
    table.add_column("Status", justify="center", width=16)

    found = empty = errors = 0

    # ── Fetching passwords with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Fetching passwords...", total=len(profiles))

        for idx, profile in enumerate(profiles, start=1):
            progress.update(
                task, description=f"[cyan]Fetching:[/cyan] [bold]{profile}[/bold]"
            )
            password = get_wifi_password(profile)

            if password == "ENCODING ERROR":
                pw_display = "[red]Encoding Error[/red]"
                status = "[bold red]⚠ Error[/bold red]"
                row_style = ""
                errors += 1
            elif password is None:
                pw_display = "[dim]── No password ──[/dim]"
                status = "[dim]No Password[/dim]"
                row_style = "dim"
                empty += 1
            else:
                pw_display = f"[bold green]{password}[/bold green]"
                status = "[bold green]✔ Found[/bold green]"
                row_style = ""
                found += 1

            table.add_row(str(idx), profile, pw_display, status, style=row_style)
            progress.advance(task)
            time.sleep(0.05)

    # ── Printing table
    console.print()
    console.print(Align.center(table))
    console.print()

    # ── Summary panel
    summary = Text(justify="center")
    summary.append(f"Total: {len(profiles)}   ", style="white")
    summary.append(f"✔ Found: {found}   ", style="bold green")
    summary.append(f"No Password: {empty}   ", style="dim")
    summary.append(f"⚠ Errors: {errors}", style="bold red")
    console.print(
        Panel(
            summary,
            title="[bold white]Summary[/bold white]",
            border_style="bright_black",
        )
    )

    # ── Footer
    console.print()
    console.print(Rule(style="dim"))
    console.print(
        "[dim]🔐 Keep your passwords safe. Do not share this output.[/dim]",
        justify="center",
    )
    console.print()
    console.input("[bold cyan]✅ Done. Press Enter to close...[/bold cyan]")


if __name__ == "__main__":
    main()
