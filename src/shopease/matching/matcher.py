"""Pure phonetic matching for Tamil and Latin customer names."""

from dataclasses import dataclass
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable, Mapping


MATCH_THRESHOLD = 0.72
AMBIGUITY_GAP = 0.08

_HONORIFICS = (
    "அண்ணாவுக்கு", "அண்ணா", "அக்காவுக்கு", "அக்கா", "தம்பிக்கு", "தம்பி",
    "anna", "akka", "thambi", "sir", "madam",
)
_SUFFIXES = ("ukku", "kku", "ku", "oda", "க்கு", "உக்கு", "ோட", "a")
_TAMIL_TO_LATIN = {
    "அ": "a", "ஆ": "aa", "இ": "i", "ஈ": "ee", "உ": "u", "ஊ": "oo",
    "எ": "e", "ஏ": "e", "ஐ": "ai", "ஒ": "o", "ஓ": "o", "ஔ": "au",
    "க": "ka", "ங": "nga", "ச": "sa", "ஜ": "ja", "ஞ": "nya", "ட": "ta",
    "ண": "na", "த": "ta", "ந": "na", "ப": "pa", "ம": "ma", "ய": "ya",
    "ர": "ra", "ல": "la", "வ": "va", "ழ": "la", "ள": "la", "ற": "ra",
    "ன": "na", "ஸ": "sa", "ஷ": "sa", "ஸ்ரீ": "sri",
    "ா": "a", "ி": "i", "ீ": "ee", "ு": "u", "ூ": "oo", "ெ": "e",
    "ே": "e", "ை": "ai", "ொ": "o", "ோ": "o", "ௌ": "au", "்": "",
}


@dataclass(frozen=True)
class Customer:
    id: int
    name: str


@dataclass(frozen=True)
class Matched:
    customer: Customer


@dataclass(frozen=True)
class Ambiguous:
    candidates: tuple[Customer, ...]


@dataclass(frozen=True)
class NoMatch:
    spoken_name: str


MatchResult = Matched | Ambiguous | NoMatch


def strip_name_parts(name: str) -> str:
    """Remove honorifics, case endings, punctuation, and extra whitespace."""
    value = unicodedata.normalize("NFC", name).strip().lower()
    value = re.sub(r"[^\w\sஅ-ஹா-ூெ-ைொ-்]", " ", value, flags=re.UNICODE)
    for honorific in _HONORIFICS:
        value = re.sub(rf"(?:^|\s){re.escape(honorific)}(?=\s|$)", " ", value)
    value = re.sub(r"(?:அண்ணா|அக்கா|தம்பி)(?:வுக்கு|க்கு)?$", "", value).strip()
    for suffix in _SUFFIXES:
        if value.endswith(suffix) and len(value) > len(suffix) + 2:
            value = value[: -len(suffix)]
            break
    return re.sub(r"\s+", " ", value).strip()


def transliterate(value: str) -> str:
    """Apply a small deterministic Tamil transliteration table."""
    output: list[str] = []
    for character in unicodedata.normalize("NFC", value):
        output.append(_TAMIL_TO_LATIN.get(character, character))
    return "".join(output).replace("ravai", "ravi").replace("tavai", "tavi")


def normalise_name(name: str) -> str:
    value = transliterate(strip_name_parts(name)).lower()
    value = re.sub(r"[^a-z0-9]", "", value)
    replacements = (
        ("th", "t"), ("dh", "t"), ("sh", "s"), ("ch", "s"),
        ("zh", "l"), ("ll", "l"), ("rr", "r"), ("nn", "n"),
        ("gh", "k"), ("kh", "k"), ("ph", "p"), ("bh", "p"),
    )
    for source, target in replacements:
        value = value.replace(source, target)
    value = re.sub(r"(.)\1+", r"\1", value)
    if len(value) > 3 and value[-1:] in {"a", "u"}:
        value = value[:-1]
    return value


def phonetic_key(name: str) -> str:
    value = normalise_name(name)
    if not value:
        return ""
    consonants = re.sub(r"[aeiou]", "", value)
    return value[0] + consonants[:5]


def _score(spoken: str, candidate: str) -> float:
    candidates = candidate.split()
    ratios = [SequenceMatcher(None, spoken, part).ratio() for part in candidates]
    ratios.append(SequenceMatcher(None, spoken, candidate).ratio())
    prefix_match = any(
        part.startswith(spoken) and len(part) - len(spoken) <= 1 for part in candidates
    )
    return max(max(ratios, default=0.0), 0.86 if prefix_match else 0.0)


def match_name(
    spoken_name: str,
    customers: Iterable[Customer],
    aliases: Mapping[str, int] | None = None,
) -> MatchResult:
    """Match a spoken name, checking aliases before phonetic candidates."""
    cleaned = normalise_name(spoken_name)
    alias_map = aliases or {}
    alias_id = alias_map.get(
        phonetic_key(spoken_name),
        alias_map.get(cleaned, alias_map.get(strip_name_parts(spoken_name).lower())),
    )
    customer_list = tuple(customers)
    if alias_id is not None:
        for customer in customer_list:
            if customer.id == alias_id:
                return Matched(customer)
    scored = sorted(
        (
            (
                max(
                    (
                        _score(cleaned, normalise_name(part))
                        for part in strip_name_parts(customer.name).split()
                    ),
                    default=_score(cleaned, normalise_name(customer.name)),
                ),
                customer,
            )
            for customer in customer_list
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not scored or scored[0][0] < MATCH_THRESHOLD:
        return NoMatch(spoken_name)
    close = tuple(customer for score, customer in scored if score >= MATCH_THRESHOLD)
    if len(close) > 1 and scored[0][0] - scored[1][0] < AMBIGUITY_GAP:
        return Ambiguous(close)
    return Matched(scored[0][1])
