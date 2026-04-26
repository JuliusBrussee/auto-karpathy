"""Optional: push the generated repo to GitHub via the gh CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def gh_available() -> bool:
    return shutil.which("gh") is not None and shutil.which("git") is not None


def push_to_github(
    project_dir: Path,
    repo_name: str,
    description: str,
    private: bool = False,
) -> str:
    """
    Init git, create GitHub repo via gh, push. Returns repo URL.

    Requires gh + git on PATH and `gh auth login` already done.
    """
    if not gh_available():
        raise RuntimeError("gh CLI not installed. brew install gh / apt install gh")

    def run(*cmd: str) -> str:
        r = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd)} failed: {r.stderr.strip()}")
        return r.stdout.strip()

    # init only if needed
    if not (project_dir / ".git").exists():
        run("git", "init", "-b", "main")
    run("git", "add", ".")
    # ok if no changes
    subprocess.run(
        ["git", "commit", "-m", "auto-karpathy: initial commit"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    visibility = "--private" if private else "--public"
    out = run(
        "gh",
        "repo",
        "create",
        repo_name,
        visibility,
        "--source",
        ".",
        "--description",
        description,
        "--push",
    )
    # gh prints the repo URL
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("https://github.com/"):
            return line
    return out
