"""Split a sentence into clauses, one per ledger action.

Tamil is verb-final, so a trigger word (கடன், கொடுத்தாங்க, cancel ...) closes
its clause. A spoken correction "<number> இல்ல <number>" keeps the second
number and is recorded on the clause that holds it.
"""

from dataclasses import dataclass
from decimal import Decimal

from shopease.contracts import IntentType
from shopease.parser.lexicon import CORRECTION_WORDS, CURRENCY, FIRST_PERSON_ENDINGS, TRIGGERS
from shopease.parser.numbers import NumberSpan, read_number
from shopease.parser.tokens import Token


@dataclass(frozen=True)
class Clause:
    tokens: tuple[Token, ...]
    trigger: IntentType | None
    corrected_amount: Decimal | None = None
    is_doubtful: bool = False  # negated ("kadan illa") or "I gave": confirm before writing


@dataclass(frozen=True)
class _Correction:
    position: int  # index of the kept number in the rewritten tokens
    amount: Decimal


def _is_first_person_give(token: Token) -> bool:
    payment_stems = dict(TRIGGERS)[IntentType.RECORD_PAYMENT]
    return token.key.startswith(payment_stems) and token.key.endswith(FIRST_PERSON_ENDINGS)


def trigger_of(token: Token) -> IntentType | None:
    if _is_first_person_give(token):
        return IntentType.ADD_CREDIT
    for intent_type, stems in TRIGGERS:
        if token.key.startswith(stems):
            return intent_type
    return None


def _skip(keys: list[str], i: int, words: frozenset[str]) -> int:
    while i < len(keys) and keys[i] in words:
        i += 1
    return i


def _correction_at(keys: list[str], i: int) -> tuple[int, NumberSpan] | None:
    """For "<number> [ரூபா] இல்ல [இல்ல] <number>" at i: where the kept number starts, and its span."""
    wrong = read_number(keys, i)
    if wrong is None:
        return None
    after_currency = _skip(keys, wrong.end, CURRENCY)
    after_illa = _skip(keys, after_currency, CORRECTION_WORDS)
    if after_illa == after_currency:
        return None
    right = read_number(keys, after_illa)
    return (after_illa, right) if right else None


def _rewrite_corrections(tokens: tuple[Token, ...]) -> tuple[tuple[Token, ...], tuple[_Correction, ...]]:
    keys = [t.key for t in tokens]
    kept: tuple[Token, ...] = ()
    corrections: tuple[_Correction, ...] = ()
    i = 0
    while i < len(tokens):
        found = _correction_at(keys, i)
        if found is None:
            kept, i = kept + (tokens[i],), i + 1
            continue
        start, right = found
        corrections = corrections + (_Correction(len(kept), right.value),)
        kept, i = kept + tokens[start : right.end], right.end
    return kept, corrections


def _tail_split(tokens: tuple[Token, ...], last_end: int) -> int:
    """Where words after the last trigger stop belonging to it.

    They join it ("kadan, rice and oil") unless a later part of the sentence
    holds a number ("kadan, Priya 100"): that part is a new, verbless clause.
    """
    trigger_segment = tokens[last_end - 1].segment
    for j in range(last_end, len(tokens)):
        if tokens[j].segment > trigger_segment and any(read_number([t.key], 0) for t in tokens[j:]):
            return j
    return len(tokens)


def _clause_ranges(tokens: tuple[Token, ...]) -> tuple[tuple[int, int], ...]:
    ends = tuple(i + 1 for i, t in enumerate(tokens) if trigger_of(t))
    if not ends:
        return ((0, len(tokens)),) if tokens else ()
    split = _tail_split(tokens, ends[-1])
    starts = (0,) + ends[:-1]
    stops = ends[:-1] + (split,)
    tail = ((split, len(tokens)),) if split < len(tokens) else ()
    return tuple(zip(starts, stops)) + tail


def _is_doubtful(tokens: tuple[Token, ...]) -> bool:
    return any(t.key in CORRECTION_WORDS or _is_first_person_give(t) for t in tokens)


def _trigger_in(tokens: tuple[Token, ...]) -> IntentType | None:
    return next((t for t in map(trigger_of, tokens) if t), None)


def split_clauses(tokens: tuple[Token, ...]) -> tuple[Clause, ...]:
    kept, corrections = _rewrite_corrections(tokens)
    clauses: tuple[Clause, ...] = ()
    for start, stop in _clause_ranges(kept):
        part = kept[start:stop]
        amount = next((c.amount for c in corrections if start <= c.position < stop), None)
        clauses = clauses + (Clause(part, _trigger_in(part), amount, _is_doubtful(part)),)
    return clauses
