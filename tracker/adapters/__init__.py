"""One adapter per recruitment platform.

Each adapter module exposes `fetch(target, http) -> list[RawJob]`.
"""

from . import (algolia, ashby, eightfold, generic, greenhouse, lever, oracle, phenom, radancy,
               recruitee, smartrecruiters, successfactors, teamtailor, workable, workday)

ADAPTERS = {
    "greenhouse": greenhouse,
    "lever": lever,
    "smartrecruiters": smartrecruiters,
    "workday": workday,
    "oracle": oracle,
    "ashby": ashby,
    "eightfold": eightfold,
    "successfactors": successfactors,
    "radancy": radancy,
    "phenom": phenom,
    "teamtailor": teamtailor,
    "workable": workable,
    "recruitee": recruitee,
    "algolia": algolia,
    "generic": generic,
}


def get_adapter(platform: str):
    try:
        return ADAPTERS[platform]
    except KeyError:
        raise ValueError(f"unknown platform '{platform}' (known: {', '.join(sorted(ADAPTERS))})")
