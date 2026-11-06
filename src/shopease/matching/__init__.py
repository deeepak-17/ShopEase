"""Phonetic name matching (Tamil and Latin script) and voice-taught aliases.

Owner: Member B
"""

from .matcher import (
    Ambiguous,
    Customer,
    Matched,
    NoMatch,
    match_name,
    normalise_name,
    phonetic_key,
)

__all__ = [
    "Ambiguous", "Customer", "Matched", "NoMatch", "match_name",
    "normalise_name", "phonetic_key",
]
