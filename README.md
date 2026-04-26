<div align="center">

# auto-karpathy

### when karpathy tweet, ape code.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Built with Claude Agent SDK](https://img.shields.io/badge/built%20with-claude--agent--sdk-D97757.svg)](https://github.com/anthropics/claude-agent-sdk-python)

```
   ┌──────────────────────────────────────────────┐
   │  karpathy tweet  →  ape watch  →  repo born  │
   └──────────────────────────────────────────────┘
```

**ape no read. ape no think. ape ship.**

</div>

---

## what this be

every week some guy on X tweet **"i built [thing] from a karpathy tweet 🚀"** and grow 10k follower.

**this tool that guy.**

`auto-karpathy` watch karpathy timeline. claude agent read tweet. claude agent build repo. you sleep. wake up. star count go up. pretend it was you.

it caveman. it cursed. it *truly work*.

> [!IMPORTANT]
> built on the official [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python). pure claude-native. no langchain in cave.

## one-line install

```bash
git clone https://github.com/JuliusBrussee/auto-karpathy && cd auto-karpathy && pipx install .
```

or, modern ape (uv):

```bash
git clone https://github.com/JuliusBrussee/auto-karpathy && cd auto-karpathy && uv tool install .
```

or, no-pipx ape (just venv):

```bash
git clone https://github.com/JuliusBrussee/auto-karpathy
cd auto-karpathy
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

then auth claude code once (`claude` itself ships in the sdk):

```bash
claude  # log in, then quit
```

done. ape ready.

## one-line use

```bash
auto-karpathy
```

that it. ape go scrape last 10 karpathy tweet, decide which one buildable, claude agent code each one into `./repos/<slug>/`, run smoke test until green.

## what it actually do

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────┐
│ scrape       │──▶│ triage agent │──▶│ builder agent │──▶│ git +   │
│ (4 sources)  │   │ (claude)     │   │ (claude+tools)│   │ gh push │
└─────────────┘   └──────────────┘   └───────────────┘   └─────────┘
```

1. **scrape** — try `syndication.twitter.com` → public nitter mirrors → optional twikit (auth) → final fallback: a claude agent with `WebFetch`+`WebSearch` that figure it out anyway.
2. **triage agent** — claude read tweet, decide: buildable idea? if yes, propose project name + slug.
3. **builder agent** — claude with `Read`/`Write`/`Edit`/`Bash` tools writes a real repo: code, README, LICENSE, smoke test, `.gitignore`, deps. **runs the smoke test until it passes.**
4. **`--push`** (optional) — runs `gh repo create … --push` so the repo lives on github before you finish your coffee.

state stored in `~/.local/state/auto-karpathy/seen.json` so `--watch` not redo same tweet.

## commands

| command | what ape do |
|---|---|
| `auto-karpathy` | one-shot. equivalent to `auto-karpathy run` |
| `auto-karpathy run` | scrape latest, triage, build the buildable ones |
| `auto-karpathy build <tweet-url>` | build from one specific tweet (forced) |
| `auto-karpathy watch --interval 600` | poll every 10 min, build new tweets forever |
| `auto-karpathy scrape` | just scrape and print. no agent. no token spend |

## flags

| flag | default | what |
|---|---|---|
| `-u, --user` | `karpathy` | any X handle. yes, you can `--user elonmusk`. ape don't judge |
| `-n, --limit` | `10` | how many recent tweets to grab |
| `-o, --output` | `./repos` | where to drop generated repos |
| `--threshold` | `0.5` | min triage confidence to build |
| `--cookies` | none | `cookies.json` for auth-backed scrape (install `auto-karpathy[auth]`) |
| `--push` | off | `gh repo create` + push every built repo |
| `--private` | off | make the pushed repos private |
| `--dry-run` | off | triage only. no build, no push. recon mode |
| `--all` | off | re-process tweets already seen |

## install variants

```bash
# default — public scraping only
git clone https://github.com/JuliusBrussee/auto-karpathy
cd auto-karpathy
pipx install .

# with twikit (auth-backed scraping if public ones get blocked)
pipx install '.[auth]'

# directly via pipx, no clone
pipx install git+https://github.com/JuliusBrussee/auto-karpathy

# editable / dev install
git clone https://github.com/JuliusBrussee/auto-karpathy
cd auto-karpathy
pip install -e '.[dev,auth]'
```

## examples

```bash
# scrape karpathy, build everything buildable, push to your github
auto-karpathy --push

# one specific tweet
auto-karpathy build https://x.com/karpathy/status/2030371219518931079

# run forever, every 10 min, push as private
auto-karpathy watch --interval 600 --push --private

# any handle. ape farm everyone now
auto-karpathy --user ylecun

# just see what would happen, don't spend tokens on building
auto-karpathy --dry-run
```

## generated repos

every repo `auto-karpathy` build come with:

- `README.md` — quotes the source tweet at the top, one-line run instruction, honest about being auto-generated
- `LICENSE` — MIT
- `.gitignore`
- runnable code (no stubs, no `pass`, builder agent forced to make it work)
- a smoke test the agent **actually runs and gets green** before finishing
- `requirements.txt` or `pyproject.toml` with pinned deps
- `SUMMARY.md` — one-paragraph explanation of what got built

if smoke test no green, builder retry up to 3 times. if still no green, repo marked `success=False` and ape move on.

## sample output

```
$ auto-karpathy

   ___       _         _  __                 _   _
  / _ \     | |       | |/ /                | | | |
 / /_\ \_   _| |_ ___  | ' / __ _ _ __ _ __ | |_| |__  _   _
 |  _  | | | | __/ _ \ |  < / _` | '__| '_ \| __| '_ \| | | |
 | | | | |_| | || (_) || . \ (_| | |  | |_) | |_| | | | |_| |
 \_| |_/\__,_|\__\___/ \_|\_\__,_|_|  | .__/ \__|_| |_|\__, |
                                      | |               __/ |
                                      |_|              |___/
            karpathy tweet -> ape code -> repo born

╭─────────────────────────────────────────────────────────╮
│ ape look at @karpathy — checking last 10 tweet          │
╰─────────────────────────────────────────────────────────╯
                       caught tweet
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ id                   ┃ text                                  ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ 2030371219518931079  │ I packaged up the "autoresearch"...  │
│ 2 │ 2029112930241001234  │ nanochat now trains GPT-2 in 2 hr... │
└───┴──────────────────────┴───────────────────────────────────────┘

──────────────── tweet 2030371219518931079 ────────────────
> I packaged up the "autoresearch" project into a new...
https://x.com/karpathy/status/2030371219518931079
ape see karpathy tweet. ape build.

triage agent thinking...
buildable=True, confidence=0.92, slug=autoresearch-mini-931079
> minimal single-GPU autoresearch repo, ~600 line one-file pytorch

builder agent coding autoresearch-mini-931079...
build ok -> ./repos/autoresearch-mini-931079 (8 files)
repo birth complete. mother proud.
```

## faq

**q: this is dystopian.**
a: yes.

**q: is this scraping legal?**
a: read X's ToS. don't be the guy who pulls 1M tweets in 24h. we hit public endpoints with normal user-agent, like every browser does. you're responsible for what you point this at.

**q: token cost?**
a: triage = 1 short turn per tweet, ~1k tokens. build = `max_turns=60` per tweet, can be 50k–200k tokens depending on project size. use `--dry-run` first. use `--threshold 0.8` to skip junk.

**q: it built broken code.**
a: builder agent runs the smoke test before declaring success. if it lied, that's a claude problem, not an ape problem. open an issue.

**q: my karpathy tweets aren't loading.**
a: install with `[auth]` extra and pass `--cookies cookies.json`. dump from your logged-in browser. ape understand.

**q: can it watch multiple users?**
a: run multiple `watch` instances in tmux. ape parallel.

**q: i actually built something useful with this.**
a: don't tell anyone where you got the idea. that's the whole point. ape collude.

## architecture

```
src/auto_karpathy/
├── cli.py        # click CLI (run / build / watch / scrape)
├── runner.py     # orchestrates scrape -> triage -> build -> push
├── scraper.py    # syndication / nitter / twikit / claude-agent fallback
├── agents.py     # triage_tweet() + build_repo() on claude-agent-sdk
├── prompts.py    # system prompts for triage and builder
├── models.py     # Tweet / TriageDecision / BuildResult (pydantic)
├── github.py     # gh repo create + push helper
├── state.py      # ~/.local/state/auto-karpathy/seen.json
└── meme.py       # banner + caveman quotes
```

## contributing

PRs welcome. ideas welcome. caveman speak welcome but optional.

```bash
git clone https://github.com/JuliusBrussee/auto-karpathy
cd auto-karpathy
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev,auth]'
pytest
```

## license

MIT. free like mass mammoth on open plain.

## related ape work

- [caveman](https://github.com/JuliusBrussee/caveman) — same ape energy, save 75% tokens
- [cavekit](https://github.com/JuliusBrussee/cavekit) — spec-driven dev, three command, no sub-agent

---

<div align="center">

if `auto-karpathy` farm karpathy idea for you, leave star.<br/>
ape star ape happy. ⭐

</div>
