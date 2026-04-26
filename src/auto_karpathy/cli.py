"""auto-karpathy CLI."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich.console import Console

from . import __version__, meme
from .runner import run_once, run_single_url, watch_loop

console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(name)s: %(message)s",
    )


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="auto-karpathy")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """auto-karpathy — when Karpathy tweet, ape code.

    \b
    Run with no args to scrape latest tweets and build buildable ones:
        auto-karpathy run

    Single tweet:
        auto-karpathy build https://x.com/karpathy/status/123

    Watch loop:
        auto-karpathy watch --interval 600
    """
    _setup_logging(verbose)
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@main.command()
@click.option("-u", "--user", default="karpathy", show_default=True, help="X handle.")
@click.option("-n", "--limit", default=10, show_default=True, help="How many recent tweets.")
@click.option(
    "-o",
    "--output",
    default="./repos",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Where to put generated repos.",
)
@click.option(
    "--cookies",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="twikit cookies.json (optional, auth-backed scrape).",
)
@click.option(
    "--threshold",
    default=0.5,
    show_default=True,
    type=float,
    help="Min triage confidence to build.",
)
@click.option("--all", "include_seen", is_flag=True, help="Re-process already-seen tweets.")
@click.option("--push", is_flag=True, help="gh repo create + push each built repo.")
@click.option("--private", is_flag=True, help="Make pushed repos private.")
@click.option("--dry-run", is_flag=True, help="Triage only, no build, no push.")
def run(
    user: str,
    limit: int,
    output: Path,
    cookies: str | None,
    threshold: float,
    include_seen: bool,
    push: bool,
    private: bool,
    dry_run: bool,
) -> None:
    """One-shot: scrape -> triage -> build."""
    console.print(meme.BANNER, style="green")
    asyncio.run(
        run_once(
            handle=user,
            limit=limit,
            output_dir=output,
            console=console,
            only_unseen=not include_seen,
            confidence_threshold=threshold,
            cookies_file=cookies,
            push=push,
            push_private=private,
            dry_run=dry_run,
        )
    )


@main.command()
@click.argument("url")
@click.option(
    "-o",
    "--output",
    default="./repos",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
)
@click.option("--push", is_flag=True)
@click.option("--private", is_flag=True)
@click.option("--dry-run", is_flag=True)
def build(url: str, output: Path, push: bool, private: bool, dry_run: bool) -> None:
    """Build a repo from a single tweet URL."""
    console.print(meme.BANNER, style="green")
    asyncio.run(
        run_single_url(
            url=url,
            output_dir=output,
            console=console,
            push=push,
            push_private=private,
            dry_run=dry_run,
        )
    )


@main.command()
@click.option("-u", "--user", default="karpathy", show_default=True)
@click.option("-n", "--limit", default=10, show_default=True)
@click.option(
    "-o",
    "--output",
    default="./repos",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
)
@click.option("--interval", default=600, show_default=True, help="Poll interval, seconds.")
@click.option("--cookies", default=None, type=click.Path(exists=True, dir_okay=False))
@click.option("--threshold", default=0.5, show_default=True, type=float)
@click.option("--push", is_flag=True)
@click.option("--private", is_flag=True)
@click.option("--dry-run", is_flag=True)
def watch(
    user: str,
    limit: int,
    output: Path,
    interval: int,
    cookies: str | None,
    threshold: float,
    push: bool,
    private: bool,
    dry_run: bool,
) -> None:
    """Watch loop. Polls every --interval seconds."""
    console.print(meme.BANNER, style="green")
    try:
        asyncio.run(
            watch_loop(
                handle=user,
                limit=limit,
                output_dir=output,
                interval_seconds=interval,
                console=console,
                confidence_threshold=threshold,
                cookies_file=cookies,
                push=push,
                push_private=private,
                dry_run=dry_run,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[bold]ape rest. tomorrow more tweet.[/bold]")


@main.command()
@click.option("-u", "--user", default="karpathy", show_default=True)
@click.option("-n", "--limit", default=10, show_default=True)
def scrape(user: str, limit: int) -> None:
    """Just scrape and print, no agents."""
    from .scraper import scrape_tweets

    tweets = asyncio.run(scrape_tweets(user, limit))
    if not tweets:
        console.print("[red]no tweets[/red]")
        sys.exit(1)
    for t in tweets:
        console.print(f"[cyan]{t.id}[/cyan]  {t.short}")


if __name__ == "__main__":
    main()
