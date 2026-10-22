"""Save raw responses of a few URLs to discovery/samples/ (development aid).

Used to write or fix an adapter when a careers site returns nothing: the HTML
is committed so the page structure can be inspected. robots.txt is honoured.

    python tools/fetch_samples.py            # URLs listed in tools/samples.txt
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tracker.http import PoliteClient  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "discovery" / "samples"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    http = PoliteClient(timeout=30)
    for line in (ROOT / "tools" / "samples.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, url = line.split(None, 1)
        try:
            resp = http.get(url, retries=0)
            body = f"<!-- {resp.status_code} {resp.url} -->\n" + resp.text[:400_000]
        except Exception as exc:
            body = f"<!-- ERROR {type(exc).__name__}: {exc} -->"
        (OUT / f"{re.sub(r'[^a-z0-9_-]', '_', name.lower())}.html").write_text(body, encoding="utf-8")
        print(name, body[:120].replace("\n", " "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
