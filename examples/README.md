# examples

example invocations. ape copy paste.

## one-shot

```bash
auto-karpathy
```

## from a single tweet URL

```bash
auto-karpathy build https://x.com/karpathy/status/2030371219518931079
```

## watch every 10 min

```bash
auto-karpathy watch --interval 600 --threshold 0.7
```

## farm a different account

```bash
auto-karpathy --user ylecun
```

## dry run (no token spend on building)

```bash
auto-karpathy --dry-run
```

## auto-push generated repos to github

```bash
gh auth login   # one-time
auto-karpathy --push --private
```

## use python instead

```python
import anyio
from pathlib import Path
from auto_karpathy.runner import run_once

anyio.run(
    lambda: run_once(
        handle="karpathy",
        limit=5,
        output_dir=Path("./repos"),
        confidence_threshold=0.7,
    )
)
```
