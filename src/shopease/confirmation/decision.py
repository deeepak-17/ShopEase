"""Pure smart-confirmation decisions."""

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Iterable

from shopease.matching.matcher import Ambiguous, NoMatch


UNUSUAL_FACTOR = Decimal("3")
MIN_HISTORY = 3
LARGE_AMOUNT = Decimal("2000")


@dataclass(frozen=True)
class Decision:
    needs_confirmation: bool
    reasons: tuple[str, ...] = ()


def decide(
    *,
    name_match: object | None,
    amount: Decimal | None,
    history: Iterable[Decimal] = (),
    parse_ambiguous: bool = False,
    has_unknown_intent: bool = False,
) -> Decision:
    reasons: list[str] = []
    if isinstance(name_match, Ambiguous):
        reasons.append("ambiguous_name")
    elif isinstance(name_match, NoMatch):
        reasons.append("new_customer")
    if amount is not None:
        values = tuple(history)
        if len(values) >= MIN_HISTORY and amount > median(values) * UNUSUAL_FACTOR:
            reasons.append("unusual_amount")
        elif len(values) < MIN_HISTORY and amount >= LARGE_AMOUNT:
            reasons.append("large_amount")
    if parse_ambiguous:
        reasons.append("ambiguous_transcript")
    if has_unknown_intent:
        reasons.append("unknown_intent")
    return Decision(bool(reasons), tuple(reasons))
