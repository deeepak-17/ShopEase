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

# (suffix, replacement) tried in order; first match wins.
_DATIVE_SUFFIXES = (("வுக்கு", ""), ("ுக்கு", "்"), ("க்கு", ""))


@dataclass(frozen=True)
class Token:
    text: str
    base: str
    is_dative: bool = False

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
            return Token(word, word[: -len(suffix)] + replacement, True)
    return Token(word, word)


def tokenize(text: str) -> tuple[Token, ...]:
    """Split normalized text; a separate Latin `ku` marks the word before it."""
    tokens: tuple[Token, ...] = ()
    for word in text.split():
        if word.casefold() in DATIVE_WORDS and tokens:
            tokens = tokens[:-1] + (replace(tokens[-1], is_dative=True),)
        else:
            tokens = tokens + (_word_token(word),)
    return tokens
