"""Stage 5: crossmatch against catalogs of known objects.

- `core`: per-signal classification (period aliases, harmonics, period-less epochs,
  transit-by-transit matching, precedence, freshness).
- `batch`: star selection (TIC ID, cone with proper-motion track) and DataFrame-level
  classification, shared by the batch crossmatch and the send-time alert gate.
- `runlevel`: run-level systematics (epoch spikes, signals shared between targets).
"""

from planethunter.crossmatch.core import (
    PARTIAL_TRANSIT_TOKEN,
    PERIODLESS_TOKEN,
    CrossmatchResult,
    KnownObject,
    MatchClass,
    Source,
    classify,
    match_period,
)

__all__ = [
    "PARTIAL_TRANSIT_TOKEN",
    "PERIODLESS_TOKEN",
    "CrossmatchResult",
    "KnownObject",
    "MatchClass",
    "Source",
    "classify",
    "match_period",
]
