from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from shopease.contracts import Intent, IntentType, ParseResult, Reply


def test_parse_result_holds_several_intents_from_one_sentence():
    result = ParseResult(
        transcript="Ravi ku 250 kadan, Priya 100 kuduthaanga",
        intents=(
            Intent(IntentType.ADD_CREDIT, spoken_name="Ravi", amount=Decimal("250")),
            Intent(IntentType.RECORD_PAYMENT, spoken_name="Priya", amount=Decimal("100")),
        ),
    )

    assert [i.type for i in result.intents] == ["add_credit", "record_payment"]


def test_contract_objects_are_immutable():
    intent = Intent(IntentType.UNDO)

    with pytest.raises(FrozenInstanceError):
        intent.amount = Decimal("1")  # type: ignore[misc]


def test_reply_defaults_to_no_confirmation():
    assert Reply(text="Ravi ku 250 add pannitten").needs_confirmation is False
