"""Short Tamil reply and reminder templates."""

from decimal import Decimal


def credit_reply(name: str, amount: Decimal, total: Decimal) -> str:
    return f"{name} அண்ணாவுக்கு {amount} ரூபாய் சேர்த்துட்டேன். மொத்தம் {total}."


def payment_reply(name: str, amount: Decimal, total: Decimal) -> str:
    return f"{name} கிட்ட {amount} ரூபாய் வாங்கிட்டேன். மீதி {total}."


def balance_reply(name: str, balance: Decimal) -> str:
    return f"{name} பாக்கி {balance} ரூபாய்."


def daily_total_reply(total: Decimal) -> str:
    return f"இன்னைக்கு வியாபாரம் {total} ரூபாய்."


def reminder_reply(name: str, balance: Decimal) -> str:
    return f"வணக்கம் {name} அண்ணா, உங்கள் பாக்கி {balance} ரூபாய். நேரம் கிடைக்கும்போது கொடுக்கவும்."


def undo_reply() -> str:
    return "கடைசி பதிவை ரத்து செய்துவிட்டேன்."
