"""Normalize a Prisma transcript and split it into tokens.

Each token keeps the word as heard (`text`) and its `base`, with the Tamil
dative suffix (-க்கு, "to") removed and recorded in `is_dative`.
"""

import re
from dataclasses import dataclass, replace

from shopease.parser.lexicon import DATIVE_WORDS, FILLERS

_DIGIT_COMMA = re.compile(r"(?<=\d),(?=\d)")
_NON_DECIMAL_DOT = re.compile(r"(?<!\d)\.|\.(?!\d)")
_PUNCTUATION = re.compile(r"[?!,;:\"'“”‘’]")
_SPACES = re.compile(r"\s+")
_BOUNDARY = re.compile(r"(?<!\d)[,.]|[,.](?!\d)|[?!;:]")

# (suffix, replacement) tried in order; first match wins.
_DATIVE_SUFFIXES = (("வுக்கு", ""), ("ுக்கு", "்"), ("க்கு", ""))


@dataclass(frozen=True)
class Token:
    text: str
    base: str
    is_dative: bool = False
    segment: int = 0  # which comma- or full-stop-separated part of the sentence

    @property
    def key(self) -> str:
        return self.base.casefold()


def normalize(transcript: str) -> str:
    """Strip punctuation, keeping digit groups (1,500) and decimals (2.5)."""
    text = _DIGIT_COMMA.sub("", transcript)
    text = text.replace("₹", " ₹ ")
    text = _NON_DECIMAL_DOT.sub(" ", text)
    text = _PUNCTUATION.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def segments(transcript: str) -> tuple[str, ...]:
    """Normalized parts of the transcript between Prisma's , . ? marks."""
    parts = (normalize(part) for part in _BOUNDARY.split(transcript.replace("₹", " ₹ ")))
    return tuple(part for part in parts if part)


def _strip_dative(word: str, suffix: str, replacement: str) -> str:
    stem = word[: -len(suffix)]
    is_doubled = len(stem) >= 3 and stem[-2] == "்" and stem[-1] == stem[-3]
    if suffix == "ுக்கு" and is_doubled:
        return stem + "ு"  # முத்துக்கு -> முத்து, not முத்த்
    return stem + replacement


def _split_hyphen(word: str) -> Token | None:
    base, _, suffix = word.partition("-")
    if not base or not suffix:
        return None
    is_dative = suffix.endswith("க்கு") or suffix.casefold() in DATIVE_WORDS
    return Token(word, base if is_dative else word, is_dative)


def _word_token(word: str) -> Token:
    if word.casefold() in FILLERS:
        return Token(word, word)
    hyphenated = _split_hyphen(word) if "-" in word else None
    if hyphenated:
        return hyphenated
    for suffix, replacement in _DATIVE_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix):
            return Token(word, _strip_dative(word, suffix, replacement), True)
    return Token(word, word)


def tokenize(text: str, segment: int = 0) -> tuple[Token, ...]:
    """Split normalized text; a separate Latin `ku` marks the word before it."""
    tokens: tuple[Token, ...] = ()
    for word in text.split():
        if word.casefold() in DATIVE_WORDS and tokens:
            tokens = tokens[:-1] + (replace(tokens[-1], is_dative=True),)
        else:
            tokens = tokens + (replace(_word_token(word), segment=segment),)
    return tokens
