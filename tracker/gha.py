"""GitHub Actions annotations, written safely.

Steps that print scraped content run with workflow commands paused
(::stop-commands::), so a job title or an error message starting with "::"
cannot be read as a command. Run summaries are therefore written to the file
named by GHA_NOTICES, which the workflow prints once commands are resumed.
Messages are escaped as GitHub requires, so they stay on one line.
"""

from __future__ import annotations

import os


def escape(text: str) -> str:
    return str(text).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def notice(title: str, lines: list[str]) -> None:
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    title = escape(title).replace(":", "%3A").replace(",", "%2C")
    command = f"::notice title={title}::" + "%0A".join(escape(line) for line in lines) + "\n"
    path = os.environ.get("GHA_NOTICES")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(command)
    else:
        print(command, end="")
