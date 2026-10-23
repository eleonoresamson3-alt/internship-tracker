"""Data structures shared by adapters and the pipeline."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Target:
    """One employer, as declared in targets.yaml."""

    name: str
    type: str
    platform: str
    careers_url: str
    params: dict = field(default_factory=dict)
    enabled: bool = True
    notes: str = ""

    @property
    def slug(self) -> str:
        return slugify(self.name)


@dataclass
class RawJob:
    """An offer as returned by an adapter, before filtering and scoring."""

    title: str
    url: str
    location: str = ""
    native_id: str = ""
    posted_at: str = ""          # ISO date when the platform exposes it
    countries: list[str] = field(default_factory=list)  # ISO 3166 alpha-2 hints
    employment_type: str = ""    # e.g. "Internship" when the platform exposes it
    description: str = ""        # short text, only when cheaply available


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def normalize_title(text: str) -> str:
    """Lower-case, accent-free, punctuation-free title used for deduplication."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
