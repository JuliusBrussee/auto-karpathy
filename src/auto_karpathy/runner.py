"""High-level orchestration: scrape -> triage -> build -> (optional) push."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import meme
from .agents import build_repo, triage_tweet
from .models import BuildResult, Tweet
from .scraper import fetch_single_tweet, scrape_tweets
from .state import load_seen, mark_seen

log = logging.getLogger(__name__)


async def run_once(
    handle: str,
    limit: int,
    output_dir: Path,
    *,
    console: Optional[Console] = None,
    only_unseen: bool = True,
    confidence_threshold: float = 0.5,
    cookies_file: Optional[str] = None,
    push: bool = False,
    push_private: bool = False,
    dry_run: bool = False,
) -> list[BuildResult]:
    console = console or Console()
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel(
            f"[bold]ape look at @{handle}[/bold] — checking last {limit} tweet",
            style="green",
        )
    )

    tweets = await scrape_tweets(handle=handle, limit=limit, cookies_file=cookies_file)
    if not tweets:
        console.print("[red]ape no find tweet. try --user or --cookies.[/red]")
        return []

    if only_unseen:
        seen = load_seen()
        new_tweets = [t for t in tweets if t.id not in seen]
        skipped = len(tweets) - len(new_tweets)
        if skipped:
            console.print(f"[dim]skip {skipped} already-seen tweet[/dim]")
        tweets = new_tweets

    if not tweets:
        console.print("[yellow]no new tweet. ape sleep.[/yellow]")
        return []

    _print_tweet_table(console, tweets)

    return await _process_tweets(
        tweets,
        output_dir,
        console=console,
        confidence_threshold=confidence_threshold,
        push=push,
        push_private=push_private,
        dry_run=dry_run,
    )


async def run_single_url(
    url: str,
    output_dir: Path,
    *,
    console: Optional[Console] = None,
    confidence_threshold: float = 0.0,  # forced build
    push: bool = False,
    push_private: bool = False,
    dry_run: bool = False,
) -> list[BuildResult]:
    console = console or Console()
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel(f"[bold]ape get one tweet[/bold]\n{url}", style="green"))
    tweet = await fetch_single_tweet(url)
    if not tweet:
        console.print("[red]ape no fetch tweet. bad url or rate limit.[/red]")
        return []
    _print_tweet_table(console, [tweet])

    return await _process_tweets(
        [tweet],
        output_dir,
        console=console,
        confidence_threshold=confidence_threshold,
        push=push,
        push_private=push_private,
        dry_run=dry_run,
    )


def _print_tweet_table(console: Console, tweets: list[Tweet]) -> None:
    tbl = Table(show_header=True, header_style="bold magenta", title="caught tweet")
    tbl.add_column("#", justify="right", width=3)
    tbl.add_column("id", style="dim", width=20)
    tbl.add_column("text")
    for i, t in enumerate(tweets, 1):
        tbl.add_row(str(i), t.id, t.short)
    console.print(tbl)


async def _process_tweets(
    tweets: list[Tweet],
    output_dir: Path,
    *,
    console: Console,
    confidence_threshold: float,
    push: bool,
    push_private: bool,
    dry_run: bool,
) -> list[BuildResult]:
    results: list[BuildResult] = []
    built_ids: list[str] = []

    for tweet in tweets:
        console.rule(f"tweet {tweet.id}")
        console.print(f"[bold]>[/bold] {tweet.short}")
        console.print(f"[dim]{tweet.url}[/dim]")
        console.print(f"[italic]{meme.random_quote()}[/italic]\n")

        with console.status("triage agent thinking..."):
            decision = await triage_tweet(tweet)

        console.print(
            f"buildable=[{'green' if decision.buildable else 'red'}]"
            f"{decision.buildable}[/], confidence={decision.confidence:.2f}, "
            f"slug=[cyan]{decision.project_slug}[/cyan]"
        )
        if decision.reasoning:
            console.print(f"[dim]{decision.reasoning}[/dim]")

        if not decision.buildable or decision.confidence < confidence_threshold:
            console.print("[yellow]ape skip. tweet too smooth-brain or too big-brain.[/yellow]")
            built_ids.append(tweet.id)  # mark seen anyway
            continue

        if dry_run:
            console.print("[blue]--dry-run: no build, no push.[/blue]")
            built_ids.append(tweet.id)
            continue

        with console.status(
            f"builder agent coding [cyan]{decision.project_slug}[/cyan]..."
        ):
            result = await build_repo(tweet, decision, output_dir)

        if result.success:
            console.print(
                f"[green]build ok[/green] -> {result.project_path} "
                f"({len(result.files_written)} files)"
            )
            console.print(f"[italic]{meme.done_quote()}[/italic]")

            if push:
                _maybe_push(
                    result,
                    decision_idea=decision.project_idea,
                    private=push_private,
                    console=console,
                )
        else:
            console.print(
                f"[red]build fail[/red] {result.error or '(no README produced)'}"
            )
            console.print(f"[italic]{meme.fail_quote()}[/italic]")

        results.append(result)
        built_ids.append(tweet.id)

    if built_ids:
        mark_seen(built_ids)

    return results


def _maybe_push(
    result: BuildResult,
    decision_idea: str,
    private: bool,
    console: Console,
) -> None:
    from .github import gh_available, push_to_github

    if not gh_available():
        console.print(
            "[yellow]gh CLI missing — skip push. install with brew/apt and `gh auth login`.[/yellow]"
        )
        return
    try:
        url = push_to_github(
            project_dir=Path(result.project_path),
            repo_name=result.project_name,
            description=decision_idea[:200],
            private=private,
        )
        console.print(f"[green]pushed:[/green] {url}")
    except Exception as e:
        console.print(f"[red]push failed:[/red] {e}")


async def watch_loop(
    handle: str,
    limit: int,
    output_dir: Path,
    interval_seconds: int,
    *,
    console: Optional[Console] = None,
    confidence_threshold: float = 0.5,
    cookies_file: Optional[str] = None,
    push: bool = False,
    push_private: bool = False,
    dry_run: bool = False,
) -> None:
    console = console or Console()
    console.print(
        f"[bold green]ape on watch[/bold green] every {interval_seconds}s "
        f"(ctrl-c to stop)"
    )
    while True:
        try:
            await run_once(
                handle=handle,
                limit=limit,
                output_dir=output_dir,
                console=console,
                confidence_threshold=confidence_threshold,
                cookies_file=cookies_file,
                push=push,
                push_private=push_private,
                dry_run=dry_run,
            )
        except Exception as e:  # don't die on transient error
            console.print(f"[red]loop error: {e}[/red]")
        await asyncio.sleep(interval_seconds)
