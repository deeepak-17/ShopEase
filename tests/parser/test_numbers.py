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
