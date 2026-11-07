import pytest

from shopease.contracts import Intent, IntentType
from shopease.parser import parse


def test_transcript_is_stored_without_punctuation():
    assert parse("அதை cancel பண்ணு.").transcript == "அதை cancel பண்ணு"


def test_several_actions_in_one_sentence():
    result = parse("Ravi ku 250 kadan Priya 100 kuduthaanga")
    assert [i.type for i in result.intents] == ["add_credit", "record_payment"]
    assert [i.spoken_name for i in result.intents] == ["Ravi", "Priya"]
    assert result.is_ambiguous is False


def test_one_ambiguous_action_marks_the_result_ambiguous():
    assert parse("Ravi ku 250 kadan ஹலோ kuduthaanga").is_ambiguous is True


@pytest.mark.parametrize("transcript", ["", "   ", "ஹலோ", "அது"])
def test_unrecognised_input_is_unknown_and_ambiguous(transcript):
    result = parse(transcript)
    assert result.intents == (Intent(IntentType.UNKNOWN),)
    assert result.is_ambiguous is True
