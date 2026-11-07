"""The 10 Prisma codemix+keywords transcripts from the Nov 2 spike, end to end."""

from decimal import Decimal

import pytest

from shopease.contracts import Intent, IntentType, Item
from shopease.parser import parse

T = IntentType

CLIPS = [
    ("Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்.", (Intent(T.ADD_CREDIT, "Ravi", Decimal("150")),), False),
    ("Ravi-க்கு எவ்வளவு பாக்கி இருக்கு?", (Intent(T.BALANCE_QUERY, "Ravi"),), False),
    ("Priya அக்கா இருநூறு ரூபாய் கொடுத்தாங்க.", (Intent(T.RECORD_PAYMENT, "Priya", Decimal("200")),), False),
    (
        "ரவிக்கு ரெண்டு கிலோ rice and oil packet, எழுநூற்றி ஐம்பது ரூபா கடன்.",
        (Intent(T.ADD_CREDIT, "ரவி", Decimal("750"), (Item("rice", Decimal("2"), "kilo"), Item("oil packet"))),),
        False,
    ),
    ("Sorry, அது இருநூத்தி அஞ்சு இல்ல, இருநூத்தம்பது.", (Intent(T.CORRECT_AMOUNT, amount=Decimal("250")),), False),
    ("அதை cancel பண்ணு.", (Intent(T.UNDO),), False),
    (
        "ஒன்றரை கிலோ sugar and கால் கிலோ tea powder முருகனுக்கு கடன்.",
        (
            Intent(
                T.ADD_CREDIT,
                "முருகன்",
                None,
                (Item("sugar", Decimal("1.5"), "kilo"), Item("tea powder", Decimal("0.25"), "kilo")),
            ),
        ),
        True,
    ),
    ("இன்னைக்கு எவ்வளோ வியாபாரம்?", (Intent(T.DAILY_TOTAL),), False),
    ("Kutty Na Karthik.", (Intent(T.TEACH_ALIAS, "Kutty", alias_target="Karthik"),), False),
    ("ரவிக்கு reminder அனுப்பு.", (Intent(T.SEND_REMINDER, "ரவி"),), False),
]


@pytest.mark.parametrize("transcript, intents, is_ambiguous", CLIPS)
def test_real_clip(transcript, intents, is_ambiguous):
    result = parse(transcript)
    assert (result.intents, result.is_ambiguous) == (intents, is_ambiguous)
