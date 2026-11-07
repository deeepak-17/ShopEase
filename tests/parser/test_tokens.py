import pytest

from shopease.parser.tokens import Token, normalize, tokenize


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்.", "Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்"),
        ("Sorry, அது இருநூத்தி அஞ்சு இல்ல, இருநூத்தம்பது.", "Sorry அது இருநூத்தி அஞ்சு இல்ல இருநூத்தம்பது"),
        ("Ravi-க்கு எவ்வளவு பாக்கி இருக்கு?", "Ravi-க்கு எவ்வளவு பாக்கி இருக்கு"),
        ("Ravi ku 1,500 kadan", "Ravi ku 1500 kadan"),
        ("₹250 கடன்", "₹ 250 கடன்"),
        ("2.5 கிலோ", "2.5 கிலோ"),
        ("  ", ""),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    "word, base, is_dative",
    [
        ("அண்ணாவுக்கு", "அண்ணா", True),
        ("ரவிக்கு", "ரவி", True),
        ("முருகனுக்கு", "முருகன்", True),
        ("பிரியாவுக்கு", "பிரியா", True),
        ("Ravi-க்கு", "Ravi", True),
        ("இன்னைக்கு", "இன்னைக்கு", False),
        ("Priya", "Priya", False),
    ],
)
def test_tokenize_strips_dative(word, base, is_dative):
    (token,) = tokenize(word)
    assert (token.base, token.is_dative) == (base, is_dative)


def test_separate_latin_ku_marks_previous_token_dative():
    assert tokenize("Ravi Kumar ku") == (
        Token("Ravi", "Ravi"),
        Token("Kumar", "Kumar", True),
    )


def test_token_key_is_casefolded():
    (token,) = tokenize("Kutty")
    assert token.key == "kutty"


def test_tokenize_empty_text():
    assert tokenize("") == ()
