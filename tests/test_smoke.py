"""Smoke tests that don't hit the network or call Claude."""

from __future__ import annotations

import pytest

from auto_karpathy import __version__
from auto_karpathy.agents import _extract_json, _normalize_slug, _slug_from_idea
from auto_karpathy.meme import done_quote, fail_quote, random_quote
from auto_karpathy.models import BuildResult, Tweet, TriageDecision
from auto_karpathy.scraper import _parse_nitter_rss, parse_tweet_url


def test_version_string() -> None:
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 1


def test_tweet_short_truncates() -> None:
    t = Tweet(id="1", url="https://x.com/karpathy/status/1", text="x" * 200)
    assert len(t.short) <= 90
    assert t.short.endswith("...")


def test_tweet_short_keeps_short_text() -> None:
    t = Tweet(id="1", url="https://x.com/karpathy/status/1", text="hello")
    assert t.short == "hello"


def test_parse_tweet_url_x() -> None:
    h, i = parse_tweet_url("https://x.com/karpathy/status/2030371219518931079")
    assert h == "karpathy"
    assert i == "2030371219518931079"


def test_parse_tweet_url_twitter() -> None:
    h, i = parse_tweet_url("twitter.com/foo/status/123")
    assert h == "foo"
    assert i == "123"


def test_parse_tweet_url_invalid() -> None:
    with pytest.raises(ValueError):
        parse_tweet_url("https://example.com/")


def test_extract_json_in_code_block() -> None:
    raw = 'prefix\n```json\n{"a": 1}\n```\ntrailing'
    assert _extract_json(raw) == {"a": 1}


def test_extract_json_bare() -> None:
    assert _extract_json('{"buildable": true}') == {"buildable": True}


def test_extract_json_invalid() -> None:
    assert _extract_json("not json at all") is None


def test_slug_helpers() -> None:
    assert _slug_from_idea("Tiny  GPT in 600 lines!") == "tiny-gpt-in-600-lines"
    assert _normalize_slug("My Slug!", "1234567890").startswith("my-slug")
    assert _normalize_slug("", "1234567890").startswith("karpathy-thing-")


def test_meme_quotes_nonempty() -> None:
    for fn in (random_quote, done_quote, fail_quote):
        s = fn()
        assert isinstance(s, str) and s


def test_models_construct() -> None:
    d = TriageDecision(tweet_id="x", buildable=True, confidence=0.7)
    assert d.confidence == 0.7
    r = BuildResult(
        tweet_id="x",
        project_path="/tmp/x",
        project_name="x",
        success=True,
    )
    assert r.success


def test_parse_nitter_rss_minimal() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss><channel>
      <item>
        <title>hello world</title>
        <link>https://nitter.net/karpathy/status/9999#m</link>
        <description><![CDATA[<p>hello world body</p>]]></description>
        <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
      </item>
    </channel></rss>"""
    out = _parse_nitter_rss(xml, "karpathy")
    assert len(out) == 1
    assert out[0].id == "9999"
    assert "hello world" in out[0].text


def test_cli_help_exits_zero() -> None:
    from click.testing import CliRunner

    from auto_karpathy.cli import main

    res = CliRunner().invoke(main, ["--help"])
    assert res.exit_code == 0
    assert "auto-karpathy" in res.output


def test_cli_subcommand_help() -> None:
    from click.testing import CliRunner

    from auto_karpathy.cli import main

    for sub in ("run", "build", "watch", "scrape"):
        res = CliRunner().invoke(main, [sub, "--help"])
        assert res.exit_code == 0, res.output
