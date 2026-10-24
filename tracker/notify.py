"""Daily digest posted on GitHub so that the repository owner gets an e-mail.

    python -m tracker.notify digest.md

Writes a Markdown digest of (1) offers whose application deadline is close and
(2) the best offers seen for the first time today. Writes nothing when there is
nothing worth a notification. The workflow posts the file as a comment on the
"recap" issue, mentioning the owner, which makes GitHub send an e-mail.

The digest cannot know which offers were already applied to (that tracking
lives only in the browser); the site hides those.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from . import config, store
from .sanitize import safe_url

DEADLINE_DAYS = 7          # deadlines within this many days are listed
DEADLINE_MIN_SCORE = 40
NEW_MIN_SCORE = 70
MAX_LINES = 20
SITE_URL = "https://eleonoresamson3-alt.github.io/internship-tracker/"


def _fr(d: str) -> str:
    y, m, day = d.split("-")
    return f"{day}/{m}/{y}"


def md_escape(text) -> str:
    """Scraped text as inert Markdown: no links, images, HTML, mentions or formatting."""
    text = " ".join(str(text or "").split())
    text = re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~])", r"\\\1", text)
    return text.replace("@", "@\u200b")    # "@name" must not notify anyone


def _line(job: dict, with_deadline: bool) -> str:
    where = job.get("location") or ", ".join(job.get("country_names", []))
    url = safe_url(job.get("url"))
    title = md_escape(job["title"])
    text = f"- **{job['score']}** · " + (f"[{title}](<{url}>)" if url else title) + f" — {md_escape(job['employer'])}"
    if where:
        text += f" ({md_escape(where[:40])})"
    if with_deadline:
        kind = "annoncée" if job.get("deadline_source") == "annonce" else "estimée"
        text += f" · clôture {kind} le **{_fr(job['deadline'])}**"
    return text


def build(jobs: list[dict], fresh: list[dict], today: date, owner: str = "") -> str:
    limit = (today + timedelta(days=DEADLINE_DAYS)).isoformat()
    soon = [j for j in jobs if j.get("active") and j.get("deadline") and today.isoformat() <= j["deadline"] <= limit
            and j["score"] >= DEADLINE_MIN_SCORE]
    # Deadlines stated in the ad first, then estimated ones; earliest first.
    soon.sort(key=lambda j: (j.get("deadline_source") != "annonce", j["deadline"], -j["score"]))
    best_new = [j for j in fresh if j["score"] >= NEW_MIN_SCORE][:MAX_LINES]
    if not soon and not best_new:
        return ""

    parts = [f"{'@' + owner + ' ' if owner else ''}récapitulatif du {_fr(today.isoformat())} · [ouvrir le tracker]({SITE_URL})", ""]
    if soon:
        parts += [f"### ⏰ Clôtures dans les {DEADLINE_DAYS} prochains jours ({len(soon)})", ""]
        parts += [_line(j, True) for j in soon[:MAX_LINES]]
        if len(soon) > MAX_LINES:
            parts.append(f"- … et {len(soon) - MAX_LINES} autres sur le site")
        parts.append("")
    if best_new:
        parts += [f"### 🆕 Meilleures nouvelles offres ({len(best_new)})", ""]
        parts += [_line(j, bool(j.get("deadline"))) for j in best_new]
        parts.append("")
    parts.append("_Dates « estimées » : calendrier habituel du type d'employeur, à vérifier sur l'annonce. "
                 "Les offres déjà postulées ou masquées n'apparaissent pas sur le site, mais ce message ne les connaît pas._")
    return "\n".join(parts) + "\n"


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    out = Path(argv[0] if argv else "digest.md")
    jobs = store.load_json(config.JOBS_FILE, {}).get("jobs", [])
    fresh = store.load_json(config.NEW_TODAY_FILE, {}).get("jobs", [])
    text = build(jobs, fresh, date.today(), os.environ.get("GITHUB_REPOSITORY_OWNER", ""))
    out.write_text(text, encoding="utf-8")
    print(f"digest: {len(text.splitlines())} lines" if text else "digest: nothing to report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
