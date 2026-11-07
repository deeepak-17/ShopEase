from decimal import Decimal

from shopease.contracts import IntentType
from shopease.parser.clauses import split_clauses
from shopease.parser.tokens import normalize, tokenize


def _clauses(text: str):
    return split_clauses(tokenize(normalize(text)))


def test_one_trigger_gives_one_clause():
    clauses = _clauses("Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்.")
    assert [c.trigger for c in clauses] == [IntentType.ADD_CREDIT]


def test_two_triggers_give_two_clauses():
    clauses = _clauses("Ravi ku 250 kadan Priya 100 kuduthaanga")
    assert [c.trigger for c in clauses] == [IntentType.ADD_CREDIT, IntentType.RECORD_PAYMENT]
    assert [t.base for t in clauses[1].tokens] == ["Priya", "100", "kuduthaanga"]


def test_trailing_words_join_last_clause():
    clauses = _clauses("Ravi anna ku 250 kadan rice and oil")
    assert len(clauses) == 1
    assert clauses[0].tokens[-1].base == "oil"


def test_spoken_correction_keeps_second_amount():
    (clause,) = _clauses("Sorry, அது இருநூத்தி அஞ்சு இல்ல, இருநூத்தம்பது.")
    assert clause.trigger is None
    assert clause.corrected_amount == Decimal("250")
    assert "இருநூத்தி" not in [t.base for t in clause.tokens]


def test_correction_inside_credit():
    (clause,) = _clauses("Ravi ku இருநூத்தி அஞ்சு இல்ல இருநூத்தம்பது kadan")
    assert clause.trigger == IntentType.ADD_CREDIT
    assert clause.corrected_amount == Decimal("250")


def test_illa_without_numbers_is_not_a_correction():
    (clause,) = _clauses("Ravi ku kadan illa")
    assert clause.trigger == IntentType.ADD_CREDIT
    assert clause.corrected_amount is None


def test_no_trigger_gives_single_untriggered_clause():
    (clause,) = _clauses("ஹலோ")
    assert clause.trigger is None


def test_empty_input_gives_no_clauses():
    assert split_clauses(()) == ()
