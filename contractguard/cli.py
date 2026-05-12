"""Command-line interface for contractguard."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from contractguard import __version__

console = Console()


@click.group()
@click.version_option(__version__, prog_name="contractguard")
def main():
    """AI agent that reads the fine print so you don't have to.

    Upload any contract and get instant analysis of red flags,
    unfair terms, and missing protections.
    """
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--model", "-m", default=None, help="LLM model to use (default: anthropic/claude-sonnet-4)")
@click.option("--api-key", "-k", envvar="OPENROUTER_API_KEY", help="API key (or set OPENROUTER_API_KEY)")
@click.option("--base-url", "-u", envvar="OPENROUTER_BASE_URL", help="API base URL")
@click.option("--output", "-o", type=click.Path(), help="Save report to file. Uses JSON when --json is set.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON instead of formatted report")
@click.option("--lang", "-l", type=click.Choice(["en", "zh"]), default="en", help="Analysis language (en or zh)")
def scan(file: str, model: str | None, api_key: str | None, base_url: str | None,
         output: str | None, json_output: bool, lang: str):
    """Scan a contract for red flags and unfair terms.

    Supports PDF, DOCX, and TXT files.

    \b
    Examples:
        contractguard scan lease.pdf
        contractguard scan contract.docx --model openai/gpt-4o
        contractguard scan nda.txt -o report.md
    """
    from contractguard.analyzer import DEFAULT_MODEL, analyze_contract
    from contractguard.parser import extract_text
    from contractguard.report import print_report

    model = model or DEFAULT_MODEL

    # Step 1: Parse document
    with console.status("[bold blue]Parsing document...[/bold blue]"):
        try:
            text = extract_text(file)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    console.print(f"[green]\u2714[/green] Parsed {Path(file).name} ({len(text):,} characters)")

    # Step 2: Analyze with LLM
    with console.status(f"[bold blue]Analyzing contract with {model}...[/bold blue]"):
        try:
            result = analyze_contract(
                contract_text=text,
                model=model,
                api_key=api_key,
                base_url=base_url,
                lang=lang,
            )
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    # Step 3: Output results
    if json_output:
        console.print(result.model_dump_json(indent=2))
    else:
        print_report(result)

    # Step 4: Save report if requested
    if output:
        _write_report(result, output, json_output=json_output)
        console.print(f"\n[green]\u2714[/green] Report saved to {output}")


@main.command()
def web():
    """Launch the web UI (requires: pip install contractguard[web])."""
    try:
        from contractguard.web import main as launch
    except ImportError:
        console.print("[red]Gradio not installed.[/red] Run: pip install contractguard[web]")
        return
    launch()


def _write_report(result, output: str, json_output: bool = False) -> None:
    from contractguard.report import generate_markdown_report

    if json_output:
        content = result.model_dump_json(indent=2) + "\n"
    else:
        content = generate_markdown_report(result)
    Path(output).write_text(content, encoding="utf-8")
