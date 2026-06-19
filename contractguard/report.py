"""Beautiful terminal report rendering using Rich."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from contractguard.batch import BatchItem, summarize_batch
from contractguard.compare import ContractComparison
from contractguard.models import AnalysisResult, Issue, Protection, Severity

console = Console()

GRADE_COLORS = {
    "A+": "bold green",
    "A": "green",
    "B+": "dark_green",
    "B": "yellow",
    "C+": "yellow",
    "C": "dark_orange",
    "D": "red",
    "F": "bold red",
}

SEVERITY_ICONS = {
    Severity.RED: "[bold red]\u2b24 RED FLAG[/bold red]",
    Severity.YELLOW: "[bold yellow]\u26a0 WARNING[/bold yellow]",
    Severity.GREEN: "[bold green]\u2714 GOOD[/bold green]",
}


def print_report(result: AnalysisResult) -> None:
    """Print a beautiful contract analysis report to the terminal."""
    console.print()

    # Header
    _print_header(result)
    console.print()

    # Summary
    _print_summary(result)
    console.print()

    # Red flags
    if result.red_flags:
        _print_issues(result.red_flags, "RED FLAGS", "red", "\u2b24")
        console.print()

    # Warnings
    if result.warnings:
        _print_issues(result.warnings, "WARNINGS", "yellow", "\u26a0")
        console.print()

    # Good clauses
    if result.good_clauses:
        _print_protections(result.good_clauses)
        console.print()

    # Missing protections
    if result.missing_protections:
        _print_missing(result.missing_protections)
        console.print()

    # Score
    _print_score(result)
    console.print()


def _print_header(result: AnalysisResult) -> None:
    """Print the report header."""
    contract_label = result.contract_type.value.replace("_", " ").upper()
    header = Text()
    header.append("\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n")
    header.append("\u2502  ", style="default")
    header.append("CONTRACTGUARD", style="bold cyan")
    header.append(" Analysis Report  \u2502\n")
    header.append(f"\u2502  Contract Type: {contract_label:<23}\u2502\n")
    header.append("\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")
    console.print(header)


def _print_summary(result: AnalysisResult) -> None:
    """Print the contract summary."""
    console.print(Panel(
        result.summary,
        title="[bold]Summary[/bold]",
        border_style="blue",
    ))

    if result.parties:
        console.print(f"  [bold]Parties:[/bold] {', '.join(result.parties)}")

    if result.key_terms:
        console.print("  [bold]Key Terms:[/bold]")
        for term in result.key_terms:
            console.print(f"    \u2022 {term}")


def _print_issues(issues: list[Issue], title: str, color: str, icon: str) -> None:
    """Print red flags or warnings."""
    console.print(f"\n[bold {color}]{icon} {title} ({len(issues)} found)[/bold {color}]")
    console.print(f"[{color}]{'=' * 50}[/{color}]")

    for i, issue in enumerate(issues, 1):
        console.print(f"\n  [bold {color}]{i}. {issue.title}[/bold {color}]")
        console.print(f"     [dim]Clause: {issue.clause}[/dim]")
        console.print(f'     [italic]"{issue.quote}"[/italic]')
        console.print(f"     {issue.explanation}")
        console.print(f"     [bold]Suggestion:[/bold] {issue.suggestion}")


def _print_protections(protections: list[Protection]) -> None:
    """Print good clauses found."""
    console.print(f"\n[bold green]\u2714 PROTECTIONS ({len(protections)} found)[/bold green]")
    console.print(f"[green]{'=' * 50}[/green]")

    for p in protections:
        console.print(f"  [green]\u2714[/green] [bold]{p.title}[/bold] ({p.clause})")
        console.print(f"    {p.explanation}")


def _print_missing(missing: list[str]) -> None:
    """Print missing protections."""
    console.print(
        f"\n[bold dark_orange]\u2753 MISSING PROTECTIONS ({len(missing)})[/bold dark_orange]"
    )
    for item in missing:
        console.print(f"  [dark_orange]\u2717[/dark_orange] {item}")


def _print_score(result: AnalysisResult) -> None:
    """Print the fairness score."""
    grade_color = GRADE_COLORS.get(result.fairness_grade, "white")
    score = result.fairness_score

    # Build score bar
    filled = score // 2
    empty = 50 - filled
    if score >= 70:
        bar_color = "green"
    elif score >= 50:
        bar_color = "yellow"
    else:
        bar_color = "red"

    # Py 3.10/3.11 don't allow backslash escapes inside f-string expressions; build pieces first.
    filled_bar = "\u2588" * filled
    empty_bar = "\u2591" * empty
    bar = f"[{bar_color}]{filled_bar}[/{bar_color}][dim]{empty_bar}[/dim]"

    console.print(Panel(
        f"  {bar}  [{grade_color}]{result.fairness_grade}[/{grade_color}]  ({score}/100)\n\n"
        f"  [bold red]{len(result.red_flags)}[/bold red] red flags  "
        f"[bold yellow]{len(result.warnings)}[/bold yellow] warnings  "
        f"[bold green]{len(result.good_clauses)}[/bold green] protections  "
        f"[bold dark_orange]{len(result.missing_protections)}[/bold dark_orange] missing",
        title="[bold]FAIRNESS SCORE[/bold]",
        border_style="cyan",
    ))


def generate_markdown_report(result: AnalysisResult) -> str:
    """Generate a markdown report string."""
    lines = [
        "# ContractGuard Analysis Report",
        "",
        f"**Contract Type:** {result.contract_type.value.replace('_', ' ').title()}",
        f"**Fairness Score:** {result.fairness_grade} ({result.fairness_score}/100)",
        f"**Parties:** {', '.join(result.parties)}",
        "",
        "## Summary",
        "",
        result.summary,
        "",
        "## Key Terms",
        "",
    ]
    for term in result.key_terms:
        lines.append(f"- {term}")

    if result.red_flags:
        lines.extend(["", "## Red Flags", ""])
        for i, issue in enumerate(result.red_flags, 1):
            lines.extend([
                f"### {i}. {issue.title}",
                "",
                f"**Clause:** {issue.clause}",
                "",
                f"> {issue.quote}",
                "",
                f"{issue.explanation}",
                "",
                f"**Suggestion:** {issue.suggestion}",
                "",
            ])

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for i, issue in enumerate(result.warnings, 1):
            lines.extend([
                f"### {i}. {issue.title}",
                "",
                f"**Clause:** {issue.clause}",
                "",
                f"> {issue.quote}",
                "",
                f"{issue.explanation}",
                "",
                f"**Suggestion:** {issue.suggestion}",
                "",
            ])

    if result.good_clauses:
        lines.extend(["", "## Protections Found", ""])
        for p in result.good_clauses:
            lines.append(f"- **{p.title}** ({p.clause}): {p.explanation}")

    if result.missing_protections:
        lines.extend(["", "## Missing Protections", ""])
        for item in result.missing_protections:
            lines.append(f"- {item}")

    return "\n".join(lines)


def print_batch_summary(items: list[BatchItem]) -> None:
    """Print a table summarizing a batch run: one row per contract, plus totals."""
    summary = summarize_batch(items)

    table = Table(title="Batch Scan Results", title_style="bold", header_style="bold")
    table.add_column("Contract")
    table.add_column("Type")
    table.add_column("Grade", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Red", justify="right")
    table.add_column("Warn", justify="right")

    for item in items:
        name = Path(item.path).name
        if item.result is None:
            table.add_row(name, "[red]error[/red]", "-", "-", "-", "-")
            continue
        result = item.result
        grade_color = GRADE_COLORS.get(result.fairness_grade, "white")
        table.add_row(
            name,
            result.contract_type.value.replace("_", " ").title(),
            f"[{grade_color}]{result.fairness_grade}[/{grade_color}]",
            f"{result.fairness_score}/100",
            str(len(result.red_flags)),
            str(len(result.warnings)),
        )

    console.print()
    console.print(table)
    console.print(
        f"\n[bold]{summary.succeeded}[/bold] analyzed"
        + (f", [red]{summary.failed} failed[/red]" if summary.failed else "")
        + f" · [bold red]{summary.total_red_flags}[/bold red] red flags"
        + f" · [bold yellow]{summary.total_warnings}[/bold yellow] warnings"
    )


def print_comparison(comparison: ContractComparison) -> None:
    """Print what changed between two analyzed versions of a contract."""
    delta = comparison.score_delta
    if delta > 0:
        arrow, color = "↑", "green"
    elif delta < 0:
        arrow, color = "↓", "red"
    else:
        arrow, color = "→", "white"

    console.print()
    console.print(Panel(
        f"Fairness: [bold]{comparison.grade_before}[/bold] ({comparison.score_before}/100)"
        f"  →  [bold]{comparison.grade_after}[/bold] ({comparison.score_after}/100)"
        f"   [{color}]{arrow} {delta:+d}[/{color}]",
        title="Contract Comparison",
        border_style=color,
    ))

    def _list(issues: list[Issue], title: str, color: str, icon: str) -> None:
        if not issues:
            return
        console.print(f"\n[bold {color}]{icon} {title}[/bold {color}]")
        for issue in issues:
            console.print(f"  [{color}]•[/{color}] {issue.title} ({issue.clause})")

    _list(comparison.resolved_red_flags, "Red flags resolved", "green", "✔")
    _list(comparison.added_red_flags, "New red flags", "red", "⬤")
    _list(comparison.resolved_warnings, "Warnings resolved", "green", "✔")
    _list(comparison.added_warnings, "New warnings", "yellow", "⚠")

    if not any([
        comparison.resolved_red_flags, comparison.added_red_flags,
        comparison.resolved_warnings, comparison.added_warnings,
    ]):
        console.print("\n[dim]No change in flagged issues between the two versions.[/dim]")
