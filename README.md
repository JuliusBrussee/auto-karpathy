<div align="center">

# 🦍 auto-karpathy

### **karpathy tweet → ape ship repo → you collect star**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Built with Claude Agent SDK](https://img.shields.io/badge/built%20with-claude--agent--sdk-D97757)](https://github.com/anthropics/claude-agent-sdk-python)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](#contributing)

`scrape karpathy timeline` · `claude agent triages tweet` · `claude agent builds working repo` · `you sleep`

```
┌──────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────┐
│   scrape     │──▶│ triage agent │──▶│ builder agent │──▶│ git push │
│  4 sources   │   │   (claude)   │   │ (claude+tools)│   │  --push  │
└──────────────┘   └──────────────┘   └───────────────┘   └──────────┘
```

**ape no read. ape no think. ape ship.**

</div>

---

## 🚀 the pitch

every week some guy on X tweets *"i built [thing] from a karpathy tweet 🚀"* and grows 10k followers.

**this tool is that guy.** it reads karpathy's timeline, picks buildable tweets, ships working repos with passing smoke tests, optionally pushes to your github. you wake up to stars. pretend it was you.

> Built on the official [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python). pure claude-native. no langchain in cave.

## ⚡ quickstart

```bash
git clone https://github.com/JuliusBrussee/auto-karpathy && cd auto-karpathy && pipx install .
claude          # auth once, then quit
auto-karpathy   # ape go.
```

<sub>that's it. ape grabs last 10 tweets, picks the buildable ones, drops repos in `./repos/<slug>/` with green smoke tests.</sub>

## 🎯 commands & flags

| command | what ape do |
|---|---|
| `auto-karpathy` | one-shot: scrape, triage, build (alias for `run`) |
| `auto-karpathy build <tweet-url>` | force-build one specific tweet |
| `auto-karpathy watch --interval 600` | poll every 10 min, build forever |
| `auto-karpathy scrape` | scrape & print only — no agent, no tokens |

| flag | default | what |
|---|---|---|
| `-u, --user` | `karpathy` | any X handle. yes, `--user elonmusk` works. ape don't judge |
| `-n, --limit` | `10` | recent tweets to grab |
| `-o, --output` | `./repos` | where to drop generated repos |
| `--threshold` | `0.5` | min triage confidence to build |
| `--cookies` | – | `cookies.json` for auth scrape (needs `[auth]` extra) |
| `--push` / `--private` | off | `gh repo create` + push (private optional) |
| `--dry-run` | off | triage only — recon mode, no token spend on builds |
| `--all` | off | re-process tweets already seen |

## 🍌 examples

```bash
auto-karpathy --push                                            # build + push public
auto-karpathy build https://x.com/karpathy/status/2030371219518931079
auto-karpathy watch --interval 600 --push --private             # forever, private
auto-karpathy --user ylecun                                     # ape farm anyone
auto-karpathy --dry-run --threshold 0.8                         # cheap recon
```

## 📦 every generated repo ships with

`README.md` quoting source tweet · `LICENSE` (MIT) · `.gitignore` · runnable code (no stubs, no `pass`) · **smoke test the agent actually runs green** · pinned deps (`requirements.txt` / `pyproject.toml`) · `SUMMARY.md`

<sub>builder retries up to 3× on red tests. if still red, repo is marked `success=False` and ape moves on.</sub>

## 🛠️ install variants

<details>
<summary><b>pipx · uv · pip · auth · dev</b> — pick your flavor</summary>

```bash
# uv (modern ape)
uv tool install .

# pipx + auth-backed scraping (twikit fallback)
pipx install '.[auth]'

# direct from github, no clone
pipx install git+https://github.com/JuliusBrussee/auto-karpathy

# dev / editable
pip install -e '.[dev,auth]'

# plain venv, no pipx
python -m venv .venv && source .venv/bin/activate && pip install -e .
```

</details>

## 🧠 how it works

1. **scrape** — `syndication.twitter.com` → public nitter mirrors → optional `twikit` (auth) → final fallback: a claude agent with `WebFetch`+`WebSearch` that figures it out anyway
2. **triage agent** — claude reads tweet, decides *buildable?* + proposes name/slug
3. **builder agent** — claude with `Read`/`Write`/`Edit`/`Bash` writes a real repo and **runs the smoke test until green**
4. **`--push`** — `gh repo create … --push` so the repo lives on github before your coffee finishes

state lives in `~/.local/state/auto-karpathy/seen.json` so `--watch` doesn't redo work.

<details>
<summary><b>sample run output</b></summary>

```
$ auto-karpathy

╭─────────────────────────────────────────────────────────╮
│ ape look at @karpathy — checking last 10 tweet          │
╰─────────────────────────────────────────────────────────╯
                       caught tweet
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ id                   ┃ text                                  ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ 2030371219518931079  │ I packaged up the "autoresearch"...  │
│ 2 │ 2029112930241001234  │ nanochat now trains GPT-2 in 2 hr... │
└───┴──────────────────────┴───────────────────────────────────────┘

──────────────── tweet 2030371219518931079 ────────────────
> I packaged up the "autoresearch" project into a new...
ape see karpathy tweet. ape build.

triage agent thinking...
buildable=True, confidence=0.92, slug=autoresearch-mini-931079
> minimal single-GPU autoresearch repo, ~600 line one-file pytorch

builder agent coding autoresearch-mini-931079...
build ok -> ./repos/autoresearch-mini-931079 (8 files)
repo birth complete. mother proud.
```

</details>

<details>
<summary><b>architecture</b></summary>

```
src/auto_karpathy/
├── cli.py        # click CLI (run / build / watch / scrape)
├── runner.py     # orchestrates scrape → triage → build → push
├── scraper.py    # syndication / nitter / twikit / claude-agent fallback
├── agents.py     # triage_tweet() + build_repo() on claude-agent-sdk
├── prompts.py    # system prompts for triage and builder
├── models.py     # Tweet / TriageDecision / BuildResult (pydantic)
├── github.py     # gh repo create + push helper
├── state.py      # ~/.local/state/auto-karpathy/seen.json
└── meme.py       # banner + caveman quotes
```

</details>

## ❓ faq

<details>
<summary><b>this is dystopian.</b></summary>yes.</details>

<details>
<summary><b>is this scraping legal?</b></summary>read X's ToS. don't pull 1M tweets in 24h. we hit public endpoints with normal user-agent like every browser. you're responsible for what you point this at.</details>

<details>
<summary><b>token cost?</b></summary>triage ≈ 1 short turn (~1k tokens) per tweet. build = <code>max_turns=60</code>, can be 50k–200k tokens depending on project size. use <code>--dry-run</code> first. raise <code>--threshold</code> to skip junk.</details>

<details>
<summary><b>it built broken code.</b></summary>builder runs the smoke test before declaring success. if it lied, that's a claude problem not an ape problem — open an issue.</details>

<details>
<summary><b>my karpathy tweets aren't loading.</b></summary>install with <code>[auth]</code> extra and pass <code>--cookies cookies.json</code>. dump from your logged-in browser. ape understand.</details>

<details>
<summary><b>can it watch multiple users?</b></summary>run multiple <code>watch</code> instances in tmux. ape parallel.</details>

<details>
<summary><b>i actually built something useful with this.</b></summary>don't tell anyone where you got the idea. that's the whole point. ape collude.</details>

## 🤝 contributing

PRs welcome. ideas welcome. caveman speak welcome but optional.

```bash
git clone https://github.com/JuliusBrussee/auto-karpathy && cd auto-karpathy
pip install -e '.[dev,auth]' && pytest
```

## 🔗 related ape work

[**caveman**](https://github.com/JuliusBrussee/caveman) — same ape energy, save 75% tokens · [**cavekit**](https://github.com/JuliusBrussee/cavekit) — spec-driven dev, three commands, no sub-agents

## 📜 license

MIT. free like mass mammoth on open plain.

---

<div align="center">

**if `auto-karpathy` farm karpathy idea for you → leave star ⭐**<br/>
<sub>ape star, ape happy.</sub>

</div>
