"""
Multi-source tweet scraper.

Strategy (each source tried in order until one returns >=1 tweet):
    1. Twitter syndication endpoint (no auth, public)
    2. Public Nitter mirrors via RSS (no auth)
    3. Final fallback: Claude agent w/ WebFetch+WebSearch
       figures it out (truly Claude-native)

The first two are zero-token. The third costs API tokens but is
unkillable as long as Claude can browse the web.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from xml.etree import ElementTree as ET

import httpx

from .models import Tweet

log = logging.getLogger(__name__)

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz",
    "https://nitter.kavin.rocks",
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Safari/605.1.15"
)


async def scrape_tweets(
    handle: str = "karpathy",
    limit: int = 10,
    cookies_file: Optional[str] = None,
) -> list[Tweet]:
    """
    Get up to `limit` recent tweets from `handle`.

    Order: syndication -> nitter -> twikit (if cookies) -> claude agent.
    """
    handle = handle.lstrip("@")

    for fn in (
        _try_syndication,
        _try_nitter,
    ):
        try:
            tweets = await fn(handle, limit)
            if tweets:
                log.info("scraper %s returned %d tweets", fn.__name__, len(tweets))
                return tweets[:limit]
        except Exception as e:
            log.warning("scraper %s failed: %s", fn.__name__, e)

    if cookies_file:
        try:
            tweets = await _try_twikit(handle, limit, cookies_file)
            if tweets:
                return tweets[:limit]
        except Exception as e:
            log.warning("twikit failed: %s", e)

    # last resort: ask Claude to scrape with WebFetch
    try:
        tweets = await _try_claude_agent(handle, limit)
        if tweets:
            return tweets[:limit]
    except Exception as e:
        log.warning("claude-agent fallback failed: %s", e)

    return []


# ---------------------------------------------------------------------------
# 1. syndication.twitter.com — public, no auth
# ---------------------------------------------------------------------------

async def _try_syndication(handle: str, limit: int) -> list[Tweet]:
    """
    Hit the public profile syndication endpoint.

    twitter widgets use this; it doesn't need auth, and returns JSON.
    """
    url = "https://syndication.twitter.com/srv/timeline-profile/screen-name/" + handle
    async with httpx.AsyncClient(
        timeout=20,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        follow_redirects=True,
    ) as client:
        r = await client.get(url)
        r.raise_for_status()
        html = r.text

    # Page embeds JSON in __NEXT_DATA__
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(?P<json>.*?)</script>',
        html,
        re.DOTALL,
    )
    if not m:
        return []
    try:
        data = json.loads(m.group("json"))
    except json.JSONDecodeError:
        return []

    entries = (
        data.get("props", {})
        .get("pageProps", {})
        .get("timeline", {})
        .get("entries", [])
    )
    tweets: list[Tweet] = []
    for entry in entries:
        content = entry.get("content", {})
        tw = content.get("tweet")
        if not tw:
            continue
        tid = str(tw.get("id_str") or tw.get("id") or "")
        text = tw.get("full_text") or tw.get("text") or ""
        if not tid or not text:
            continue
        created = tw.get("created_at")
        try:
            ca = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y") if created else None
        except (ValueError, TypeError):
            ca = None
        tweets.append(
            Tweet(
                id=tid,
                url=f"https://x.com/{handle}/status/{tid}",
                text=text,
                author=handle,
                created_at=ca,
            )
        )
        if len(tweets) >= limit:
            break
    return tweets


# ---------------------------------------------------------------------------
# 2. Nitter RSS — multiple instances
# ---------------------------------------------------------------------------

async def _try_nitter(handle: str, limit: int) -> list[Tweet]:
    async with httpx.AsyncClient(
        timeout=15,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        for base in NITTER_INSTANCES:
            try:
                r = await client.get(f"{base}/{handle}/rss")
                if r.status_code != 200 or "<rss" not in r.text:
                    continue
                tweets = _parse_nitter_rss(r.text, handle)
                if tweets:
                    return tweets[:limit]
            except Exception:
                continue
    return []


def _parse_nitter_rss(xml: str, handle: str) -> list[Tweet]:
    out: list[Tweet] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return out
    channel = root.find("channel")
    if channel is None:
        return out
    for item in channel.findall("item"):
        link = (item.findtext("link") or "").strip()
        # nitter link looks like https://nitter.net/karpathy/status/1234#m
        m = re.search(r"/status/(\d+)", link)
        if not m:
            continue
        tid = m.group(1)
        title = (item.findtext("title") or "").strip()
        # title contains "R to ..." for replies; we keep the text as-is
        # description is HTML; strip tags
        desc_html = item.findtext("description") or ""
        text = re.sub(r"<[^>]+>", "", desc_html).strip() or title
        pub = item.findtext("pubDate")
        try:
            ca = (
                datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").replace(
                    tzinfo=timezone.utc
                )
                if pub
                else None
            )
        except ValueError:
            ca = None
        out.append(
            Tweet(
                id=tid,
                url=f"https://x.com/{handle}/status/{tid}",
                text=text,
                author=handle,
                created_at=ca,
            )
        )
    return out


# ---------------------------------------------------------------------------
# 3. twikit (auth) — optional
# ---------------------------------------------------------------------------

async def _try_twikit(handle: str, limit: int, cookies_file: str) -> list[Tweet]:
    try:
        from twikit import Client  # type: ignore
    except ImportError:
        log.warning("twikit not installed (pip install 'auto-karpathy[auth]')")
        return []

    client = Client("en-US")
    client.load_cookies(cookies_file)
    user = await client.get_user_by_screen_name(handle)
    raw = await client.get_user_tweets(user.id, "Tweets", count=limit)
    out: list[Tweet] = []
    for tw in raw:
        try:
            ca = datetime.strptime(tw.created_at, "%a %b %d %H:%M:%S %z %Y")
        except (ValueError, TypeError, AttributeError):
            ca = None
        out.append(
            Tweet(
                id=str(tw.id),
                url=f"https://x.com/{handle}/status/{tw.id}",
                text=tw.text,
                author=handle,
                created_at=ca,
            )
        )
    return out


# ---------------------------------------------------------------------------
# 4. Claude-native fallback — agent w/ WebFetch + WebSearch
# ---------------------------------------------------------------------------

CLAUDE_SCRAPE_PROMPT = """\
You are a tweet scraping agent. Your job: fetch the {limit} most recent
tweets from @{handle} on X/Twitter and return them as JSON.

Try sources in order until one works:
1. https://nitter.net/{handle}
2. https://nitter.privacydev.net/{handle}
3. https://x.com/{handle}
4. WebSearch for "site:x.com from:{handle}" sorted by date

Return ONLY a JSON code block, no other text:

```json
{{
  "tweets": [
    {{"id": "1234567890", "url": "https://x.com/{handle}/status/1234567890",
      "text": "tweet text here"}}
  ]
}}
```

Skip retweets and replies to others. Keep only original posts.
If you cannot retrieve any tweets, return: ```json
{{"tweets": []}}
```
"""


async def _try_claude_agent(handle: str, limit: int) -> list[Tweet]:
    try:
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            TextBlock,
            query,
        )
    except ImportError:
        return []

    options = ClaudeAgentOptions(
        allowed_tools=["WebFetch", "WebSearch"],
        max_turns=10,
        system_prompt="You return only JSON. No prose.",
    )
    text_chunks: list[str] = []
    async for msg in query(
        prompt=CLAUDE_SCRAPE_PROMPT.format(handle=handle, limit=limit),
        options=options,
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    text_chunks.append(block.text)

    raw = "\n".join(text_chunks)
    m = re.search(r"```json\s*(?P<j>\{.*?\})\s*```", raw, re.DOTALL)
    payload = m.group("j") if m else raw
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    out: list[Tweet] = []
    for t in data.get("tweets", []):
        try:
            out.append(
                Tweet(
                    id=str(t["id"]),
                    url=t.get("url") or f"https://x.com/{handle}/status/{t['id']}",
                    text=t["text"],
                    author=handle,
                )
            )
        except KeyError:
            continue
    return out


# ---------------------------------------------------------------------------
# Single-tweet by URL
# ---------------------------------------------------------------------------

TWEET_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:x|twitter)\.com/(?P<handle>[^/]+)/status/(?P<id>\d+)"
)


def parse_tweet_url(url: str) -> tuple[str, str]:
    m = TWEET_URL_RE.search(url)
    if not m:
        raise ValueError(f"not a tweet URL: {url}")
    return m.group("handle"), m.group("id")


async def fetch_single_tweet(url: str) -> Optional[Tweet]:
    handle, tid = parse_tweet_url(url)
    # Try syndication endpoint for a single tweet
    syn_url = "https://cdn.syndication.twimg.com/tweet-result?id=" + tid + "&token=a"
    async with httpx.AsyncClient(
        timeout=15,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        try:
            r = await client.get(syn_url)
            if r.status_code == 200:
                d = r.json()
                text = d.get("text") or d.get("full_text") or ""
                if text:
                    return Tweet(
                        id=tid,
                        url=f"https://x.com/{handle}/status/{tid}",
                        text=text,
                        author=handle,
                    )
        except Exception:
            pass

    # fall back to scraping the timeline and filtering
    timeline = await scrape_tweets(handle, limit=50)
    for t in timeline:
        if t.id == tid:
            return t
    return None


def sync_scrape(handle: str = "karpathy", limit: int = 10) -> list[Tweet]:
    """Sync wrapper for ergonomics."""
    return asyncio.run(scrape_tweets(handle, limit))
