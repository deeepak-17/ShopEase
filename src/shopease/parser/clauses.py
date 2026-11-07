"""Split a sentence into clauses, one per ledger action.

Tamil is verb-final, so a trigger word (கடன், கொடுத்தாங்க, cancel ...) closes
its clause. A spoken correction "<number> இல்ல <number>" keeps the second
number and is recorded on the clause that holds it.
"""

from dataclasses import dataclass
from decimal import Decimal

from shopease.contracts import IntentType
from shopease.parser.lexicon import CORRECTION_WORDS, TRIGGERS
from shopease.parser.numbers import read_number
from shopease.parser.tokens import Token


@dataclass(frozen=True)
class Clause:
    tokens: tuple[Token, ...]
    trigger: IntentType | None
    corrected_amount: Decimal | None = None


@dataclass(frozen=True)
class _Correction:
    position: int  # index of the kept number in the rewritten tokens
    amount: Decimal


def trigger_of(token: Token) -> IntentType | None:
    for intent_type, stems in TRIGGERS:
        if token.key.startswith(stems):
            return intent_type
    return None


def _rewrite_corrections(tokens: tuple[Token, ...]) -> tuple[tuple[Token, ...], tuple[_Correction, ...]]:
    keys = [t.key for t in tokens]
    kept: tuple[Token, ...] = ()
    corrections: tuple[_Correction, ...] = ()
    i = 0
    while i < len(tokens):
        wrong = read_number(keys, i)
        is_correction = wrong is not None and wrong.end < len(keys) and keys[wrong.end] in CORRECTION_WORDS
        right = read_number(keys, wrong.end + 1) if is_correction else None
        if right is None:
            kept, i = kept + (tokens[i],), i + 1
            continue
        corrections = corrections + (_Correction(len(kept), right.value),)
        kept, i = kept + tokens[wrong.end + 1 : right.end], right.end
    return kept, corrections


def _clause_ranges(tokens: tuple[Token, ...]) -> tuple[tuple[int, int], ...]:
    ends = tuple(i + 1 for i, t in enumerate(tokens) if trigger_of(t))
    if not ends:
        return ((0, len(tokens)),) if tokens else ()
    starts = (0,) + ends[:-1]
    stops = ends[:-1] + (len(tokens),)  # trailing words join the last clause
    return tuple(zip(starts, stops))


def _trigger_in(tokens: tuple[Token, ...]) -> IntentType | None:
    return next((t for t in map(trigger_of, tokens) if t), None)


def split_clauses(tokens: tuple[Token, ...]) -> tuple[Clause, ...]:
    kept, corrections = _rewrite_corrections(tokens)
    clauses: tuple[Clause, ...] = ()
    for start, stop in _clause_ranges(kept):
        part = kept[start:stop]
        amount = next((c.amount for c in corrections if start <= c.position < stop), None)
        clauses = clauses + (Clause(part, _trigger_in(part), amount),)
    return clauses
