"""Sentences from the PR #22 review that wrote a wrong debt, direction or name."""

from decimal import Decimal

import pytest

from shopease.contracts import Intent, IntentType
from shopease.parser import parse
from shopease.parser.tokens import tokenize


@pytest.mark.parametrize("transcript", ["Ravi ku 200 kadan illa", "Ravi 500 kuduthaar illa"])
def test_negated_action_is_ambiguous(transcript):
    assert parse(transcript).is_ambiguous is True


@pytest.mark.parametrize("transcript", ["Ravi ku 200 கொடுத்தேன்", "ரவிக்கு 200 குடுத்தேன்", "Ravi ku 200 kuduthen"])
def test_i_gave_is_credit_not_payment(transcript):
    result = parse(transcript)
    assert result.intents[0].type == IntentType.ADD_CREDIT
    assert result.intents[0].amount == Decimal("200")
    assert result.is_ambiguous is True


@pytest.mark.parametrize(
    "transcript, name",
    [
        ("இன்னிக்கு Ravi ku 200 kadan", "Ravi"),
        ("நாளைக்கு Ravi 500 குடுத்தாரு", "Ravi"),
        ("அதுக்கு Ravi 200 kadan", "Ravi"),
        ("நேத்து Ravi 500 குடுத்தாரு", "Ravi"),
        ("Ravi cash 500 kuduthaar", "Ravi"),
        ("Ravi gpay la 500 kuduthaar", "Ravi"),
    ],
)
def test_time_and_payment_words_are_not_the_name(transcript, name):
    result = parse(transcript)
    assert result.intents[0].spoken_name == name
    assert result.intents[0].items == ()


def test_pronoun_is_not_a_name():
    result = parse("அவருக்கு 200 கடன்")
    assert result.intents[0].spoken_name is None
    assert result.is_ambiguous is True


def test_extra_unknown_words_in_a_payment_are_ambiguous():
    assert parse("Ravi ஏதோ 500 kuduthaar").is_ambiguous is True


def test_three_word_name_is_ambiguous():
    assert parse("Ravi Kumar Swamy ku 300 kadan").is_ambiguous is True


@pytest.mark.parametrize("word, base", [("முத்துக்கு", "முத்து"), ("முருகனுக்கு", "முருகன்")])
def test_dative_keeps_names_ending_in_u(word, base):
    assert tokenize(word)[0].base == base


@pytest.mark.parametrize(
    "transcript",
    ["Ravi ku 200 ரூபா இல்ல 300 ரூபா kadan", "Ravi ku இருநூறு இல்ல இல்ல முன்னூறு kadan"],
)
def test_correction_with_currency_or_repeated_illa(transcript):
    result = parse(transcript)
    assert result.intents[0].amount == Decimal("300")
    assert result.is_ambiguous is False


def test_number_after_a_comma_starts_a_new_action():
    result = parse("Ravi ku 200 kadan, Priya 100")
    assert result.intents == (
        Intent(IntentType.ADD_CREDIT, "Ravi", Decimal("200")),
        Intent(IntentType.UNKNOWN, "Priya", Decimal("100")),
    )
    assert result.is_ambiguous is True


def test_items_after_a_comma_stay_with_the_credit():
    result = parse("Ravi anna ku 250 kadan, rice and oil")
    assert [i.name for i in result.intents[0].items] == ["rice", "oil"]
    assert len(result.intents) == 1


def test_no_verb_keeps_name_and_amount():
    result = parse("Ravi ku 250")
    assert result.intents == (Intent(IntentType.UNKNOWN, "Ravi", Decimal("250")),)
    assert result.is_ambiguous is True
