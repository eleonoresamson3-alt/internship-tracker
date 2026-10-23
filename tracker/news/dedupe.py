"""Group articles telling the same story, and keep a 30-day history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .classify import normalize

STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "at", "by", "with", "as", "is", "are",
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "en", "a", "au", "aux", "pour", "sur",
    "par", "dans", "avec", "est", "sont", "que", "qui", "se", "sa", "son", "ses", "its", "it", "after",
    "apres", "says", "dit", "new", "nouveau", "nouvelle",
}
SIMILARITY = 0.6   # share of common significant words for two titles to be the same story


def title_words(title: str) -> set[str]:
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w) > 1}


def similar(a: str, b: str) -> bool:
    wa, wb = title_words(a), title_words(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= SIMILARITY and len(wa & wb) >= 3


def cluster(items: list[dict]) -> list[list[dict]]:
    """Greedy grouping of similar titles (items are dicts with a "title")."""
    groups: list[list[dict]] = []
    for item in items:
        for group in groups:
            if similar(item["title"], group[0]["title"]):
                group.append(item)
                break
        else:
            groups.append([item])
    return groups


def merge_history(history: list[dict], fresh: list[dict], now: datetime, keep_days: int = 30) -> list[dict]:
    """Add today's articles to the history: same link or same story keeps the
    first record (first_seen, sources merged); records older than keep_days go."""
    by_id = {item["id"]: item for item in history}
    for item in fresh:
        old = by_id.get(item["id"]) or next((h for h in by_id.values() if similar(h["title"], item["title"])), None)
        if old:
            old["sources"] = sorted(set(old.get("sources", [])) | set(item["sources"]))
            old["score"] = max(old["score"], item["score"])
            continue
        by_id[item["id"]] = item
    cutoff = (now - timedelta(days=keep_days)).isoformat()
    kept = [i for i in by_id.values() if (i.get("published") or i["first_seen"]) >= cutoff]
    kept.sort(key=lambda i: i.get("published") or i["first_seen"], reverse=True)
    return kept


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
