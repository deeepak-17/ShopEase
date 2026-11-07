from decimal import Decimal

import pytest

from shopease.parser.numbers import NumberSpan, is_number_word, read_number


@pytest.mark.parametrize(
    "words, value, end",
    [
        (["நூற்றம்பது"], "150", 1),  # clip 01
        (["இருநூறு"], "200", 1),  # clip 03
        (["எழுநூற்றி", "ஐம்பது"], "750", 2),  # clip 04
        (["இருநூத்தி", "அஞ்சு"], "205", 2),  # clip 05
        (["இருநூத்தம்பது"], "250", 1),  # clip 05
        (["ஒன்றரை"], "1.5", 1),  # clip 07
        (["கால்"], "0.25", 1),  # clip 07
        (["அரை"], "0.5", 1),
        (["ரெண்டு"], "2", 1),  # clip 04
        (["நூத்தி", "அம்பது"], "150", 2),
        (["நூற்றைம்பது"], "150", 1),
        (["ஆயிரத்தி", "ஐநூறு"], "1500", 2),
        (["ரெண்டாயிரம்"], "2000", 1),
        (["ரெண்டு", "ஆயிரம்"], "2000", 2),
        (["இருபத்தஞ்சு"], "25", 1),
        (["நூறு", "இருநூறு"], "100", 1),  # adjacent amounts do not merge
        (["250"], "250", 1),
        (["2.5"], "2.5", 1),
        (["nooru", "aimbadhu"], "150", 2),  # issue #3 example
        (["onnara"], "1.5", 1),
    ],
)
def test_read_number(words, value, end):
    assert read_number(words, 0) == NumberSpan(Decimal(value), end)


def test_read_number_returns_none_for_non_number_word():
    assert read_number(["கிலோ"], 0) is None


def test_read_number_starts_at_offset():
    assert read_number(["ரவிக்கு", "ரெண்டு", "கிலோ"], 1) == NumberSpan(Decimal("2"), 2)


def test_is_number_word():
    assert is_number_word("நூற்றம்பது")
    assert is_number_word("250")
    assert not is_number_word("rice")


@pytest.mark.parametrize(
    "words, value, end",
    [
        (["ரெண்டு", "நூறு"], "200", 2),  # review #21: unit x hundred
        (["மூணு", "நூத்தி", "அம்பது"], "350", 3),
        (["இருவது"], "20", 1),  # colloquial tens
        (["அறுவது"], "60", 1),
        (["எழுவது"], "70", 1),
        (["எம்பது"], "80", 1),
        (["தொன்னூறு"], "90", 1),
        (["பத்தொம்பது"], "19", 1),
        (["இருவத்தஞ்சு"], "25", 1),
        (["எம்பத்தஞ்சு"], "85", 1),
        (["ஒரு"], "1", 1),
        (["ரெண்டே", "கால்"], "2.25", 2),
        (["ஒன்னே", "முக்கால்"], "1.75", 2),
        (["ஒன்னேகால்"], "1.25", 1),
        (["முக்கா"], "0.75", 1),
        (["பத்து", "ஆயிரம்"], "10000", 2),
        (["பத்தாயிரம்"], "10000", 1),
        (["இருபதாயிரம்"], "20000", 1),
        (["ரெண்டரை", "ஆயிரம்"], "2500", 2),
        (["2", "ஆயிரம்"], "2000", 2),  # digits mixed with words
        (["ஆயிரத்து", "500"], "1500", 2),
        (["100", "200"], "100", 1),
        (["20", "5"], "20", 1),  # two digit groups never merge
        (["ரெண்டு", "அரை"], "2.5", 2),  # pinned: "two and a half", not two halves
        (["தொண்ணூத்தஞ்சு"], "95", 1),
        (["ஆயிரத்திருநூறு"], "1200", 1),
        (["நூத்தி", "பத்து"], "110", 2),
        (["நூத்தி"], "100", 1),  # join form at end of input
    ],
)
def test_read_spoken_variants(words, value, end):
    assert read_number(words, 0) == NumberSpan(Decimal(value), end)


def test_read_number_rejects_negative_start():
    assert read_number(["ரெண்டு"], -1) is None


def test_digits_must_match_whole_word():
    assert not is_number_word("250\n")


@pytest.mark.parametrize(
    "words, value, end",
    [
        (["ஐநூறு", "2", "கிலோ"], "500", 1),  # review #22: a quantity after an amount
        (["ஆயிரம்", "5"], "1000", 1),
        (["2", "அரை"], "2", 1),
    ],
)
def test_digit_after_full_number_word_starts_a_new_number(words, value, end):
    assert read_number(words, 0) == NumberSpan(Decimal(value), end)
