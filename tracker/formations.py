"""Trainings and certifications of the "Formations" tab.

    python -m tracker.formations OUT.json    # validate config/formations.yaml and write it as JSON for the site
    python -m tracker.formations --check     # validate only

The list lives in config/formations.yaml so it can be edited by hand; personal
progress is never stored here (browser localStorage only).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

from . import config

FORMATIONS_FILE = config.ROOT / "config" / "formations.yaml"
CATEGORIES = {
    "certification_reglementaire": "Certification réglementaire",
    "marches": "Marchés",
    "code": "Code",
    "maths_financieres": "Maths financières",
    "risque": "Risque",
}
FIELDS = ("id", "nom", "organisme", "categorie", "priorite", "heures", "cout", "lien", "competences",
          "utilite", "echeance", "echeance_libelle", "verifie_le", "a_verifier", "cv")
_ID = re.compile(r"[a-z0-9][a-z0-9-]*$")


def _date(value) -> str | None:
    """YAML dates come as date objects, quoted ones as strings; both become AAAA-MM-JJ."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    date.fromisoformat(text)  # raises ValueError if malformed
    return text


def load(path: Path = FORMATIONS_FILE) -> tuple[list[dict], list[str]]:
    """Normalised formations and the problems found (empty when the file is valid)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items, problems, seen = [], [], set()
    for n, raw in enumerate(data.get("formations") or []):
        where = f"formation {n + 1} ({raw.get('nom') or raw.get('id') or '?'})" if isinstance(raw, dict) else f"formation {n + 1}"
        if not isinstance(raw, dict):
            problems.append(f"{where}: expected a mapping")
            continue
        unknown = set(raw) - set(FIELDS)
        if unknown:
            problems.append(f"{where}: unknown field(s) {', '.join(sorted(unknown))}")
        item = {k: raw.get(k) for k in FIELDS}
        if not item["id"] or not _ID.match(str(item["id"])):
            problems.append(f"{where}: id must be lowercase letters, digits and dashes")
        elif item["id"] in seen:
            problems.append(f"{where}: id {item['id']!r} used twice")
        seen.add(item["id"])
        if not item["nom"]:
            problems.append(f"{where}: nom is required")
        if item["categorie"] not in CATEGORIES:
            problems.append(f"{where}: categorie must be one of {', '.join(CATEGORIES)}")
        if item["priorite"] not in (1, 2, 3):
            problems.append(f"{where}: priorite must be 1, 2 or 3")
        if item["heures"] not in (None, "") and not isinstance(item["heures"], (int, float)):
            problems.append(f"{where}: heures must be a number (or empty)")
        for key in ("echeance", "verifie_le"):
            try:
                item[key] = _date(item[key])
            except ValueError:
                problems.append(f"{where}: {key} must be a date AAAA-MM-JJ")
                item[key] = None
        for key in ("competences", "a_verifier"):
            value = item[key] or []
            item[key] = [str(v) for v in value] if isinstance(value, list) else [str(value)]
        for key in ("organisme", "cout", "lien", "utilite", "echeance_libelle", "cv"):
            item[key] = str(item[key]).strip() if item[key] not in (None, "") else ""
        item["heures"] = item["heures"] if item["heures"] not in ("",) else None
        items.append(item)
    return items, problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", nargs="?", help="JSON file to write for the site")
    parser.add_argument("--check", action="store_true", help="validate only")
    args = parser.parse_args(argv)
    items, problems = load()
    for p in problems:
        print("problem:", p)
    if problems:
        return 1
    if args.out and not args.check:
        Path(args.out).write_text(json.dumps({"categories": CATEGORIES, "formations": items},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ok: {len(items)} formation(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
