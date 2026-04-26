from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Tweet(BaseModel):
    """One tweet, normalized across scraper backends."""

    id: str
    url: str
    text: str
    author: str = "karpathy"
    created_at: Optional[datetime] = None
    media: list[str] = Field(default_factory=list)

    @property
    def short(self) -> str:
        t = self.text.replace("\n", " ").strip()
        return t if len(t) <= 90 else t[:87] + "..."


class TriageDecision(BaseModel):
    """Triage agent verdict on a tweet."""

    tweet_id: str
    buildable: bool
    confidence: float = Field(ge=0.0, le=1.0)
    project_idea: str = ""
    project_slug: str = ""
    reasoning: str = ""


class BuildResult(BaseModel):
    """Builder agent result."""

    tweet_id: str
    project_path: str
    project_name: str
    success: bool
    files_written: list[str] = Field(default_factory=list)
    error: Optional[str] = None
