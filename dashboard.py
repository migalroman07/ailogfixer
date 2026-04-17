from rich.console import Console
from rich.table import Table
from sqlalchemy import select

from database import Incident, SessionLocal


def run_dashboard():
    db = SessionLocal()
    incidents = db.scalars(
        select(Incident).order_by(Incident.id.desc()).limit(10)
    ).all()
    db.close()

    console = Console()
    table = Table(title="SRE AI Dashboard", show_header=True, header_style="bold cyan")

    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Status", width=12)
    table.add_column("System Log", style="dim", width=45)
    table.add_column("AI Commands", style="green")

    if not incidents:
        console.print("[yellow]База данных пуста. Задач нет.[/yellow]")
        return

    for incident in incidents:
        if incident.status == "resolved":
            status_str = "[bold green]RESOLVED[/]"
        elif incident.status == "processing":
            status_str = "[bold yellow]PROCESSING[/]"
        else:
            status_str = "[bold red]PENDING[/]"

        log_text = incident.raw_log.replace("\n", " ")
        ai_text = incident.ai_summary if incident.ai_summary else "Ожидает обработки"

        table.add_row(str(incident.id), status_str, log_text, ai_text)

    console.print(table)


if __name__ == "__main__":
    run_dashboard()
