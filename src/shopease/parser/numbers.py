"""Tamil number words, as Prisma's codemix output writes them, to Decimal.

Handles spoken and formal spellings, fused forms (நூற்றம்பது = 150),
join forms followed by another word (எழுநூற்றி ஐம்பது = 750), fractions
(அரை, கால், ஒன்றரை), digits, and a few romanized base words.
"""

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

UNIT, TEN, HUNDRED, THOUSAND, FRACTION = 1, 10, 100, 1000, 0

_UNITS = {
    "ஒன்று": 1, "ஒன்னு": 1, "ஒரு": 1, "ஒண்ணு": 1, "ரெண்டு": 2, "இரண்டு": 2,
    "மூணு": 3, "மூன்று": 3, "நாலு": 4, "நான்கு": 4, "அஞ்சு": 5, "ஐந்து": 5,
    "ஆறு": 6, "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "ஒம்பது": 9,
}
_TEENS = {
    "பத்து": 10, "பதினொன்னு": 11, "பதினொன்று": 11, "பன்னெண்டு": 12,
    "பன்னிரண்டு": 12, "பதிமூணு": 13, "பதின்மூன்று": 13, "பதினாலு": 14,
    "பதினான்கு": 14, "பதினஞ்சு": 15, "பதினைந்து": 15, "பதினாறு": 16,
    "பதினேழு": 17, "பதினெட்டு": 18, "பத்தொன்பது": 19, "பத்தொம்பது": 19,
}
_TENS = {
    "இருபது": 20, "முப்பது": 30, "நாற்பது": 40, "நாப்பது": 40, "ஐம்பது": 50,
    "அம்பது": 50, "அறுபது": 60, "எழுபது": 70, "எண்பது": 80, "தொண்ணூறு": 90,
    "இருவது": 20, "அறுவது": 60, "எழுவது": 70, "எம்பது": 80, "தொன்னூறு": 90,
}
_HUNDREDS = {
    "நூறு": 100, "இருநூறு": 200, "முன்னூறு": 300, "நானூறு": 400,
    "ஐநூறு": 500, "அறுநூறு": 600, "எழுநூறு": 700, "எண்ணூறு": 800,
    "தொள்ளாயிரம்": 900,
}
_THOUSANDS = {
    "ஆயிரம்": 1000, "ரெண்டாயிரம்": 2000, "மூவாயிரம்": 3000,
    "நாலாயிரம்": 4000, "அஞ்சாயிரம்": 5000, "ஐயாயிரம்": 5000,
    "ஆறாயிரம்": 6000, "ஏழாயிரம்": 7000, "எட்டாயிரம்": 8000,
    "ஒம்பதாயிரம்": 9000,
}
_FRACTIONS = {"அரை": "0.5", "கால்": "0.25", "முக்கால்": "0.75", "முக்கா": "0.75"}
_ROMANIZED = {
    "onnu": ("1", UNIT), "rendu": ("2", UNIT), "moonu": ("3", UNIT),
    "naalu": ("4", UNIT), "anju": ("5", UNIT), "pathu": ("10", TEN),
    "irupadhu": ("20", TEN), "aimbadhu": ("50", TEN), "ambadhu": ("50", TEN),
    "nooru": ("100", HUNDRED), "irunooru": ("200", HUNDRED),
    "ainooru": ("500", HUNDRED), "ezhunooru": ("700", HUNDRED),
    "aayiram": ("1000", THOUSAND), "arai": ("0.5", FRACTION),
    "kaal": ("0.25", FRACTION), "mukkaal": ("0.75", FRACTION),
    "onnara": ("1.5", FRACTION),
}

# Independent vowel -> the vowel sign it becomes after a consonant.
VOWEL_SIGN = {
    "அ": "", "ஆ": "ா", "இ": "ி", "ஈ": "ீ", "உ": "ு", "ஊ": "ூ",
    "எ": "ெ", "ஏ": "ே", "ஐ": "ை", "ஒ": "ொ", "ஓ": "ோ",
}
_DIGITS = re.compile(r"\d+(\.\d+)?")

Form = tuple[Decimal, int]  # (value, place)


@dataclass(frozen=True)
class NumberSpan:
    value: Decimal
    end: int


def _base_forms() -> dict[str, Form]:
    groups = ((_UNITS, UNIT), (_TEENS, TEN), (_TENS, TEN), (_HUNDREDS, HUNDRED), (_THOUSANDS, THOUSAND))
    forms = {word: (Decimal(value), place) for table, place in groups for word, value in table.items()}
    forms |= {word: (Decimal(value), FRACTION) for word, value in _FRACTIONS.items()}
    return forms


def _stems(word: str, value: Decimal, place: int) -> tuple[str, ...]:
    """Spellings of a round number that another number word can follow."""
    if place < TEN or value % place:
        return ()
    if word.endswith("று"):
        return (word[:-2] + "ற்ற", word[:-2] + "த்த")
    if word.endswith(("பது", "வது")):
        return (word[:-1] + "்த",)
    if word.endswith("ம்"):
        return (word[:-2] + "த்த",)
    return ()


def _compound_forms(bases: Mapping[str, Form]) -> Iterator[tuple[str, Form]]:
    tails = [(w, f) for w, f in bases.items() if w[0] in VOWEL_SIGN and f[1] != FRACTION]
    for word, (value, place) in bases.items():
        for stem in _stems(word, value, place):
            yield stem + "ி", (value, place)  # join form: நூத்தி
            yield stem + "ு", (value, place)  # join form: ஆயிரத்து
            for tail, (tail_value, tail_place) in tails:
                if tail_value < place:
                    yield stem + VOWEL_SIGN[tail[0]] + tail[1:], (value + tail_value, tail_place)


def _half_forms() -> Iterator[tuple[str, Form]]:
    for word, value in _UNITS.items():
        if word.endswith("ு"):
            yield word[:-1] + "ரை", (Decimal(value) + Decimal("0.5"), FRACTION)


def _emphatic_forms() -> Iterator[tuple[str, Form]]:
    """ரெண்டே (2, before கால்), and fused ஒன்னேகால் 1.25."""
    for word, value in _UNITS.items():
        if word.endswith("ு"):
            yield word[:-1] + "ே", (Decimal(value), UNIT)
            for fraction, part in _FRACTIONS.items():
                yield word[:-1] + "ே" + fraction, (Decimal(value) + Decimal(part), FRACTION)


def _thousand_forms() -> Iterator[tuple[str, Form]]:
    """பத்தாயிரம் 10000, இருபதாயிரம் 20000: a number ending in ு, fused with ஆயிரம்."""
    for table in (_UNITS, _TEENS, _TENS):
        for word, value in table.items():
            if word.endswith("ு"):
                yield word[:-1] + "ாயிரம்", (Decimal(value) * THOUSAND, THOUSAND)


def _build_forms() -> Mapping[str, Form]:
    bases = _base_forms()
    romanized = {w: (Decimal(v), p) for w, (v, p) in _ROMANIZED.items()}
    generated = (
        dict(_compound_forms(bases)) | dict(_half_forms()) | dict(_emphatic_forms()) | dict(_thousand_forms())
    )
    return MappingProxyType(generated | romanized | bases)


_FORMS = _build_forms()


def _digit_place(value: Decimal) -> int:
    return next(place for place in (UNIT, TEN, HUNDRED) if value < place * 10) if value < THOUSAND else THOUSAND


def _form(word: str) -> Form | None:
    if _DIGITS.fullmatch(word):
        value = Decimal(word)
        return value, _digit_place(value)
    return _FORMS.get(word)


def is_number_word(word: str) -> bool:
    """True for a Tamil number word, a romanized one, or digits."""
    return _form(word) is not None


def _multiplies(total: Decimal, last_place: int, value: Decimal, place: int) -> bool:
    """ரெண்டு நூறு = 200, பத்து ஆயிரம் = 10000: a smaller number times நூறு/ஆயிரம்."""
    return place in (HUNDRED, THOUSAND) and value == place and total < place and last_place < place


def read_number(words: Sequence[str], start: int) -> NumberSpan | None:
    """Read the longest number starting at words[start], or None."""
    first = _form(words[start]) if 0 <= start < len(words) else None
    if first is None:
        return None
    total, last_place = first
    end = start + 1
    while end < len(words) and (form := _form(words[end])) is not None:
        if _DIGITS.fullmatch(words[end - 1]) and _DIGITS.fullmatch(words[end]):
            break  # two digit groups are two numbers
        value, place = form
        if _multiplies(total, last_place, value, place):
            total, last_place = total * place, place
        elif place < last_place:
            total, last_place = total + value, place
        else:
            break
        end += 1
    return NumberSpan(total, end)
