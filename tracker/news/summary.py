"""Optional daily summary written by Claude (off unless ANTHROPIC_API_KEY is set).

    python -m tracker.news.summary

Reads data/news.json, sends the day's most important headlines and the week's
main stories to the Anthropic API, and writes data/news_summary.json:
a 200-word French summary (5 facts to know and what they imply for rates,
volatility and structured products) and 3 possible interview questions.
Without the secret, or if the call fails, nothing is written and the site
simply shows no summary.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

from .. import config, store

MODEL = "claude-opus-5-5"
MAX_DAY_ITEMS = 40
MAX_WEEK_ITEMS = 30

SYSTEM = (
    "Tu aides une étudiante qui prépare des entretiens de stage en pricing, structuring et modélisation "
    "financière. À partir des titres d'actualité fournis, et uniquement d'eux, tu écris en français. "
    "N'invente aucun chiffre ni aucun fait absent des titres et résumés."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Environ 200 mots : les 5 faits à connaître aujourd'hui, puis ce qu'ils impliquent "
                           "pour les taux, la volatilité et les produits structurés. Markdown simple autorisé.",
        },
        "questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3 questions d'entretien possibles sur l'actualité de la semaine.",
        },
    },
    "required": ["summary", "questions"],
    "additionalProperties": False,
}


def _lines(items: list[dict]) -> str:
    return "\n".join(f"- [{i['source']}] {i['title']}" + (f" — {i['summary'][:200]}" if i.get("summary") else "")
                     for i in items)


def build_prompt(items: list[dict], now: datetime) -> str | None:
    day_cut = (now - timedelta(hours=24)).isoformat()[:16]
    week_cut = (now - timedelta(days=7)).isoformat()[:16]
    when = lambda i: i.get("published") or i["first_seen"]
    day = sorted((i for i in items if when(i) >= day_cut), key=lambda i: -i["score"])[:MAX_DAY_ITEMS]
    week = sorted((i for i in items if week_cut <= when(i) < day_cut), key=lambda i: -i["score"])[:MAX_WEEK_ITEMS]
    if not day:
        return None
    return (f"Titres des dernières 24 heures (les plus importants d'abord) :\n{_lines(day)}\n\n"
            f"Autres titres importants de la semaine :\n{_lines(week) or '- (aucun)'}\n\n"
            "Écris le résumé du jour et les 3 questions d'entretien.")


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("summary: ANTHROPIC_API_KEY not set, skipped")
        return 0
    import anthropic  # imported only when the option is on

    now = datetime.now(timezone.utc)
    items = store.load_json(config.NEWS_FILE, {}).get("items", [])
    prompt = build_prompt(items, now)
    if prompt is None:
        print("summary: no article in the last 24 hours, skipped")
        return 0

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            # If the request is declined by a safety classifier, the API retries it on a fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError as exc:
        print(f"summary: network error, skipped ({exc})")
        return 0
    except anthropic.APIStatusError as exc:
        print(f"summary: API error {exc.status_code}, skipped ({exc.message})")
        return 0

    if response.stop_reason == "refusal":
        print("summary: request declined, skipped")
        return 0
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"summary: unexpected output (stop_reason={response.stop_reason}), skipped")
        return 0

    store.save_json(config.NEWS_SUMMARY_FILE, {
        "generated_at": now.isoformat(timespec="seconds"),
        "model": response.model,
        "summary": data["summary"],
        "questions": data["questions"][:3],
        "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
    })
    print(f"summary: written ({response.usage.input_tokens} input / {response.usage.output_tokens} output tokens)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
