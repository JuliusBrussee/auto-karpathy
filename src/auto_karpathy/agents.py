"""Triage + builder agents wired up on the Claude Agent SDK."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import AsyncIterator, Optional

from .models import BuildResult, TriageDecision, Tweet
from .prompts import (
    BUILDER_SYSTEM,
    TRIAGE_SYSTEM,
    builder_user_prompt,
    triage_user_prompt,
)

log = logging.getLogger(__name__)

JSON_RE = re.compile(r"```json\s*(?P<j>\{.*?\})\s*```", re.DOTALL)


def _extract_json(text: str) -> Optional[dict]:
    m = JSON_RE.search(text)
    payload = m.group("j") if m else text
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


async def _collect_text(stream: AsyncIterator) -> str:
    """Concatenate all assistant TextBlocks from an SDK stream."""
    from claude_agent_sdk import AssistantMessage, TextBlock

    chunks: list[str] = []
    async for msg in stream:
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------

async def triage_tweet(tweet: Tweet) -> TriageDecision:
    """Ask Claude whether this tweet is a buildable idea."""
    from claude_agent_sdk import ClaudeAgentOptions, query

    options = ClaudeAgentOptions(
        system_prompt=TRIAGE_SYSTEM,
        allowed_tools=[],
        max_turns=1,
    )

    raw = await _collect_text(
        query(
            prompt=triage_user_prompt(tweet.text, tweet.url),
            options=options,
        )
    )
    data = _extract_json(raw) or {}

    return TriageDecision(
        tweet_id=tweet.id,
        buildable=bool(data.get("buildable", False)),
        confidence=float(data.get("confidence", 0.0)),
        project_idea=str(data.get("project_idea", "")),
        project_slug=_normalize_slug(
            data.get("project_slug") or _slug_from_idea(data.get("project_idea", "")),
            tweet.id,
        ),
        reasoning=str(data.get("reasoning", "")),
    )


def _slug_from_idea(idea: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", idea.lower()).strip("-")
    return s[:40] or "karpathy-thing"


def _normalize_slug(slug: str, tweet_id: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    if not s:
        s = "karpathy-thing"
    return f"{s}-{tweet_id[-6:]}"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

async def build_repo(
    tweet: Tweet,
    decision: TriageDecision,
    output_dir: Path,
    max_turns: int = 60,
) -> BuildResult:
    """Spawn a builder agent that writes a working repo into output_dir/<slug>."""
    from claude_agent_sdk import ClaudeAgentOptions, query

    project_dir = output_dir / decision.project_slug
    project_dir.mkdir(parents=True, exist_ok=True)

    options = ClaudeAgentOptions(
        system_prompt=BUILDER_SYSTEM,
        cwd=str(project_dir),
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        max_turns=max_turns,
    )

    prompt = builder_user_prompt(
        tweet_text=tweet.text,
        tweet_url=tweet.url,
        project_idea=decision.project_idea,
        project_slug=decision.project_slug,
        project_dir=str(project_dir),
    )

    error: Optional[str] = None
    try:
        await _collect_text(query(prompt=prompt, options=options))
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        log.exception("builder failed for tweet %s", tweet.id)

    files = sorted(
        str(p.relative_to(project_dir))
        for p in project_dir.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )

    success = error is None and (project_dir / "README.md").exists()

    return BuildResult(
        tweet_id=tweet.id,
        project_path=str(project_dir),
        project_name=decision.project_slug,
        success=success,
        files_written=files,
        error=error,
    )
