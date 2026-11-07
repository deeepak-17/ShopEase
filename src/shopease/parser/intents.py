"""Build one ledger Intent from a clause: name, amount and items."""

from dataclasses import dataclass
from decimal import Decimal

from shopease.contracts import Intent, IntentType, Item
from shopease.parser.clauses import Clause, trigger_of
from shopease.parser.lexicon import (
    ALIAS_WORDS, CORRECTION_WORDS, CURRENCY, FILLERS, HONORIFICS, ITEM_JOINERS, UNITS,
)
from shopease.parser.numbers import NumberSpan, is_number_word, read_number
from shopease.parser.tokens import Token

_KNOWN_WORDS = HONORIFICS | FILLERS | CURRENCY | ITEM_JOINERS | CORRECTION_WORDS | ALIAS_WORDS | frozenset(UNITS)
_NEEDS_NAME = frozenset({
    IntentType.ADD_CREDIT, IntentType.RECORD_PAYMENT, IntentType.BALANCE_QUERY, IntentType.SEND_REMINDER,
})
_NEEDS_AMOUNT = frozenset({IntentType.ADD_CREDIT, IntentType.RECORD_PAYMENT})


@dataclass(frozen=True)
class BuiltIntent:
    intent: Intent
    is_ambiguous: bool


@dataclass(frozen=True)
class _Located:
    position: int
    item: Item


def _is_word(token: Token) -> bool:
    """A word the lexicon does not know: part of a name or an item."""
    return token.key not in _KNOWN_WORDS and not is_number_word(token.key) and trigger_of(token) is None


def _run_end(tokens: tuple[Token, ...], start: int) -> int:
    end = start
    while end < len(tokens) and _is_word(tokens[end]) and not tokens[end].is_dative:
        end += 1
    return end


def _join(tokens: tuple[Token, ...]) -> str:
    return " ".join(t.base for t in tokens)


def _number_spans(keys: list[str]) -> tuple[tuple[int, NumberSpan], ...]:
    spans: tuple[tuple[int, NumberSpan], ...] = ()
    i = 0
    while i < len(keys):
        span = read_number(keys, i)
        spans, i = (spans + ((i, span),), span.end) if span else (spans, i + 1)
    return spans


def _items(tokens: tuple[Token, ...], spans) -> tuple[tuple[_Located, ...], frozenset[int]]:
    """Items with a quantity (ரெண்டு கிலோ rice) or after a joiner (and oil packet)."""
    keys = [t.key for t in tokens]
    starts = {start: span for start, span in spans}
    found: tuple[_Located, ...] = ()
    used: frozenset[int] = frozenset()
    i = 0
    while i < len(tokens):
        span = starts.get(i)
        if span and span.end < len(tokens) and keys[span.end] in UNITS:
            end = _run_end(tokens, span.end + 1)
            if end > span.end + 1:
                item = Item(_join(tokens[span.end + 1 : end]), span.value, UNITS[keys[span.end]])
                found = found + (_Located(i, item),)
            used, i = used | frozenset(range(i, end)), end
            continue
        if keys[i] in ITEM_JOINERS and _run_end(tokens, i + 1) > i + 1:
            end = _run_end(tokens, i + 1)
            found = found + (_Located(i + 1, Item(_join(tokens[i + 1 : end]))),)
            used, i = used | frozenset(range(i, end)), end
            continue
        i = span.end if span else i + 1
    return found, used


def _amount(keys: list[str], spans, used: frozenset[int]) -> tuple[Decimal | None, bool]:
    """The amount and whether choosing it was a guess."""
    free = [(start, span) for start, span in spans if start not in used]
    marked = [
        span for start, span in free
        if (span.end < len(keys) and keys[span.end] in CURRENCY) or (start > 0 and keys[start - 1] in CURRENCY)
    ]
    candidates = marked or [span for _, span in free]
    if not candidates:
        return None, False
    return (candidates[0] if marked else candidates[-1]).value, len(candidates) > 1


def _name_range(tokens: tuple[Token, ...], used: frozenset[int]) -> range:
    """Words of the name: the run ending at the first dative, else the first run."""
    def is_free_word(i: int) -> bool:
        return i not in used and _is_word(tokens[i])

    dative = next((i for i, t in enumerate(tokens) if t.is_dative), None)
    if dative is not None:
        end = dative if tokens[dative].key in HONORIFICS else dative + 1
        start = end
        while start > 0 and is_free_word(start - 1) and (start == end or not tokens[start - 1].is_dative):
            start -= 1
        return range(start, end)
    first = next((i for i in range(len(tokens)) if is_free_word(i)), None)
    if first is None:
        return range(0)
    end = first
    while end < len(tokens) and is_free_word(end):
        end += 1
    return range(first, end)


def _leftover_items(tokens: tuple[Token, ...], taken: frozenset[int]) -> tuple[_Located, ...]:
    found: tuple[_Located, ...] = ()
    i = 0
    while i < len(tokens):
        if i in taken or not _is_word(tokens[i]):
            i += 1
            continue
        end = i
        while end < len(tokens) and end not in taken and _is_word(tokens[end]):
            end += 1
        found, i = found + (_Located(i, Item(_join(tokens[i:end]))),), end
    return found


def _alias(clause: Clause) -> Intent | None:
    tokens = clause.tokens
    split = next((i for i, t in enumerate(tokens) if t.key in ALIAS_WORDS), None)
    if clause.trigger is not None or split is None or split == 0 or split == len(tokens) - 1:
        return None
    if not all(_is_word(t) for i, t in enumerate(tokens) if i != split):
        return None
    return Intent(IntentType.TEACH_ALIAS, spoken_name=_join(tokens[:split]), alias_target=_join(tokens[split + 1 :]))


def _triggered(clause: Clause, kind: IntentType) -> BuiltIntent:
    tokens = clause.tokens
    keys = [t.key for t in tokens]
    spans = _number_spans(keys)
    located, used = _items(tokens, spans)
    amount, is_guess = _amount(keys, spans, used)
    if clause.corrected_amount is not None:
        amount, is_guess = clause.corrected_amount, False
    names = _name_range(tokens, used)
    name = _join(tokens[names.start : names.stop]) or None
    if kind == IntentType.ADD_CREDIT:
        located = located + _leftover_items(tokens, used | frozenset(names))
    items = tuple(x.item for x in sorted(located, key=lambda x: x.position))
    intent = Intent(
        kind,
        spoken_name=name if kind in _NEEDS_NAME else None,
        amount=amount if kind in _NEEDS_AMOUNT else None,
        items=items if kind == IntentType.ADD_CREDIT else (),
    )
    is_missing = (kind in _NEEDS_NAME and name is None) or (kind in _NEEDS_AMOUNT and amount is None)
    return BuiltIntent(intent, is_missing or (kind in _NEEDS_AMOUNT and is_guess))


def build_intent(clause: Clause) -> BuiltIntent:
    alias = _alias(clause)
    if alias:
        return BuiltIntent(alias, False)
    if clause.trigger is None and clause.corrected_amount is not None:
        return BuiltIntent(Intent(IntentType.CORRECT_AMOUNT, amount=clause.corrected_amount), False)
    if clause.trigger is None:
        return BuiltIntent(Intent(IntentType.UNKNOWN), True)
    return _triggered(clause, clause.trigger)
