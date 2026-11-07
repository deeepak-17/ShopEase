from decimal import Decimal

from shopease.confirmation import decide
from shopease.matching import Customer, NoMatch


def test_normal_amount_does_not_confirm():
    assert not decide(
        name_match=object(), amount=Decimal("100"), history=(Decimal("100"),) * 3
    ).needs_confirmation


def test_unusual_amount_confirms():
    decision = decide(
        name_match=object(), amount=Decimal("500"), history=(Decimal("100"),) * 3
    )
    assert decision.reasons == ("unusual_amount",)


def test_new_customer_confirms():
    decision = decide(name_match=NoMatch("Suresh"), amount=Decimal("50"))
    assert decision.needs_confirmation
