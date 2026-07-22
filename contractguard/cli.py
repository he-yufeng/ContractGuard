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
@click.option("--output", "-o", type=click.Path(), help="Save report to file (.html writes self-contained HTML)")
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
@click.argument("path", type=click.Path(exists=True))
@click.option("--model", "-m", default=None, help="LLM model to use (default: anthropic/claude-sonnet-4)")
@click.option("--api-key", "-k", envvar="OPENROUTER_API_KEY", help="API key (or set OPENROUTER_API_KEY)")
@click.option("--base-url", "-u", envvar="OPENROUTER_BASE_URL", help="API base URL")
@click.option("--lang", "-l", type=click.Choice(["en", "zh"]), default="en", help="Analysis language (en or zh)")
@click.option("--output-dir", "-o", type=click.Path(), help="Save a markdown report per contract into this directory.")
def batch(path: str, model: str | None, api_key: str | None, base_url: str | None,
          lang: str, output_dir: str | None):
    """Scan multiple contracts at once: a folder (searched recursively) or a single file.

    \b
    Examples:
        contractguard batch ./contracts/
        contractguard batch ./contracts/ -o reports/
    """
    from contractguard.analyzer import DEFAULT_MODEL, analyze_contract
    from contractguard.batch import BatchItem, analyze_paths, discover_contracts
    from contractguard.parser import extract_text
    from contractguard.report import generate_markdown_report, print_batch_summary

    model = model or DEFAULT_MODEL
    paths = discover_contracts(path)
    if not paths:
        console.print("[yellow]No supported contract files found.[/yellow]")
        return

    console.print(f"[bold blue]Scanning {len(paths)} contract(s)...[/bold blue]")

    def _analyze(p: Path) -> object:
        return analyze_contract(
            contract_text=extract_text(p),
            model=model,
            api_key=api_key,
            base_url=base_url,
            lang=lang,
        )

    def _progress(item: BatchItem) -> None:
        name = Path(item.path).name
        if item.ok:
            console.print(f"[green]✔[/green] {name}")
        else:
            console.print(f"[red]✘[/red] {name}: {item.error}")

    items = analyze_paths(paths, _analyze, on_result=_progress)
    print_batch_summary(items)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for item in items:
            if item.result is None:
                continue
            (out / (Path(item.path).stem + ".md")).write_text(
                generate_markdown_report(item.result), encoding="utf-8"
            )
        console.print(f"\n[green]✔[/green] Reports saved to {output_dir}")


@main.command()
@click.argument("before", type=click.Path(exists=True))
@click.argument("after", type=click.Path(exists=True))
@click.option("--model", "-m", default=None, help="LLM model to use (default: anthropic/claude-sonnet-4)")
@click.option("--api-key", "-k", envvar="OPENROUTER_API_KEY", help="API key (or set OPENROUTER_API_KEY)")
@click.option("--base-url", "-u", envvar="OPENROUTER_BASE_URL", help="API base URL")
@click.option("--lang", "-l", type=click.Choice(["en", "zh"]), default="en", help="Analysis language (en or zh)")
def compare(before: str, after: str, model: str | None, api_key: str | None,
            base_url: str | None, lang: str):
    """Compare two versions of a contract and show what changed.

    \b
    Examples:
        contractguard compare lease-v1.pdf lease-v2.pdf
    """
    from contractguard.analyzer import DEFAULT_MODEL, analyze_contract
    from contractguard.compare import compare_results
    from contractguard.parser import extract_text
    from contractguard.report import print_comparison

    model = model or DEFAULT_MODEL

    def _analyze(path: str, label: str) -> object:
        with console.status(f"[bold blue]Analyzing {label}...[/bold blue]"):
            try:
                return analyze_contract(
                    contract_text=extract_text(path),
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    lang=lang,
                )
            except Exception as e:
                console.print(f"[bold red]Error analyzing {label}:[/bold red] {e}")
                sys.exit(1)

    before_result = _analyze(before, Path(before).name)
    after_result = _analyze(after, Path(after).name)
    print_comparison(compare_results(before_result, after_result))


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
    from contractguard.html import generate_html_report
    from contractguard.report import generate_markdown_report

    if json_output:
        content = result.model_dump_json(indent=2) + "\n"
    elif output.lower().endswith((".html", ".htm")):
        content = generate_html_report(result)
    else:
        content = generate_markdown_report(result)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
