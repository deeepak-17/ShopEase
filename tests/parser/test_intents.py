from decimal import Decimal

from shopease.contracts import Intent, IntentType, Item
from shopease.parser.clauses import split_clauses
from shopease.parser.intents import build_intent
from shopease.parser.tokens import normalize, tokenize


def _build(text: str):
    return build_intent(split_clauses(tokenize(normalize(text)))[0])


def test_credit_with_honorific_and_dative():
    built = _build("Ravi அண்ணாவுக்கு நூற்றம்பது ரூபா கடன்.")
    assert built.intent == Intent(IntentType.ADD_CREDIT, spoken_name="Ravi", amount=Decimal("150"))
    assert built.is_ambiguous is False


def test_payment_takes_first_name():
    built = _build("Priya அக்கா இருநூறு ரூபாய் கொடுத்தாங்க.")
    assert built.intent == Intent(IntentType.RECORD_PAYMENT, spoken_name="Priya", amount=Decimal("200"))


def test_items_with_quantity_and_without():
    built = _build("ரவிக்கு ரெண்டு கிலோ rice and oil packet, எழுநூற்றி ஐம்பது ரூபா கடன்.")
    assert built.intent == Intent(
        IntentType.ADD_CREDIT,
        spoken_name="ரவி",
        amount=Decimal("750"),
        items=(Item("rice", Decimal("2"), "kilo"), Item("oil packet")),
    )
    assert built.is_ambiguous is False


def test_fraction_items_and_missing_amount_is_ambiguous():
    built = _build("ஒன்றரை கிலோ sugar and கால் கிலோ tea powder முருகனுக்கு கடன்.")
    assert built.intent == Intent(
        IntentType.ADD_CREDIT,
        spoken_name="முருகன்",
        amount=None,
        items=(Item("sugar", Decimal("1.5"), "kilo"), Item("tea powder", Decimal("0.25"), "kilo")),
    )
    assert built.is_ambiguous is True


def test_trailing_items_after_trigger():
    built = _build("Ravi anna ku 250 kadan rice and oil")
    assert built.intent == Intent(
        IntentType.ADD_CREDIT,
        spoken_name="Ravi",
        amount=Decimal("250"),
        items=(Item("rice"), Item("oil")),
    )


def test_alias():
    built = _build("Kutty Na Karthik.")
    assert built.intent == Intent(IntentType.TEACH_ALIAS, spoken_name="Kutty", alias_target="Karthik")
    assert built.is_ambiguous is False


def test_multi_word_name_with_latin_ku():
    built = _build("Ravi Kumar ku 300 kadan")
    assert built.intent.spoken_name == "Ravi Kumar"
    assert built.intent.amount == Decimal("300")


def test_digits_with_currency_symbol():
    assert _build("₹250 Ravi ku kadan").intent.amount == Decimal("250")


def test_two_bare_amounts_are_ambiguous():
    assert _build("Ravi ku 100 200 kadan").is_ambiguous is True


def test_correction_amount():
    built = _build("Sorry, அது இருநூத்தி அஞ்சு இல்ல, இருநூத்தம்பது.")
    assert built.intent == Intent(IntentType.CORRECT_AMOUNT, amount=Decimal("250"))
    assert built.is_ambiguous is False


def test_undo_and_daily_total_need_no_name():
    assert _build("அதை cancel பண்ணு.").intent == Intent(IntentType.UNDO)
    assert _build("இன்னைக்கு எவ்வளோ வியாபாரம்?").intent == Intent(IntentType.DAILY_TOTAL)


def test_balance_and_reminder_take_dative_name():
    assert _build("Ravi-க்கு எவ்வளவு பாக்கி இருக்கு?").intent == Intent(IntentType.BALANCE_QUERY, spoken_name="Ravi")
    assert _build("ரவிக்கு reminder அனுப்பு.").intent == Intent(IntentType.SEND_REMINDER, spoken_name="ரவி")


def test_balance_without_name_is_ambiguous():
    assert _build("எவ்வளவு பாக்கி").is_ambiguous is True


def test_no_trigger_is_unknown_and_ambiguous():
    built = _build("ஹலோ")
    assert built.intent == Intent(IntentType.UNKNOWN)
    assert built.is_ambiguous is True
