from datetime import datetime, timezone
from decimal import Decimal
import sqlite3
import threading

from shopease.contracts import Intent, IntentType, ParseResult
from shopease.ledger import LedgerRepository, SQLiteLedger


def make_ledger() -> SQLiteLedger:
    repository = LedgerRepository(
        sqlite3.connect(":memory:"),
        now=lambda: datetime(2026, 11, 6, tzinfo=timezone.utc),
    )
    ledger = SQLiteLedger(repository)
    ledger.add_customer("Ravi Kumar", 1)
    return ledger


def apply(ledger: SQLiteLedger, intent: Intent, text: str = "command"):
    return ledger.apply(ParseResult(text, (intent,)))


def test_credit_payment_and_balance():
    ledger = make_ledger()
    apply(ledger, Intent(IntentType.ADD_CREDIT, "Ravi", Decimal("250")))
    apply(ledger, Intent(IntentType.RECORD_PAYMENT, "Ravi", Decimal("100")))
    reply = apply(ledger, Intent(IntentType.BALANCE_QUERY, "Ravi"))
    assert "150" in reply.text


def test_correction_replaces_and_undo_voids_latest():
    ledger = make_ledger()
    apply(ledger, Intent(IntentType.ADD_CREDIT, "Ravi", Decimal("205")))
    apply(ledger, Intent(IntentType.CORRECT_AMOUNT, amount=Decimal("250")))
    assert "250" in apply(ledger, Intent(IntentType.BALANCE_QUERY, "Ravi")).text
    apply(ledger, Intent(IntentType.UNDO))
    assert "0" in apply(ledger, Intent(IntentType.BALANCE_QUERY, "Ravi")).text


def test_daily_total_uses_exact_paise_conversion():
    ledger = make_ledger()
    apply(ledger, Intent(IntentType.ADD_CREDIT, "Ravi", Decimal("1.25")))
    assert "1.25" in apply(ledger, Intent(IntentType.DAILY_TOTAL)).text


def test_reminder_does_not_require_an_amount():
    ledger = make_ledger()
    apply(ledger, Intent(IntentType.ADD_CREDIT, "Ravi", Decimal("250")))

    reply = apply(ledger, Intent(IntentType.SEND_REMINDER, "Ravi"))

    assert "Ravi" in reply.text
    assert "250" in reply.text


def test_yes_confirmation_adds_new_customer_and_entry():
    ledger = make_ledger()
    first = apply(ledger, Intent(IntentType.ADD_CREDIT, "Suresh", Decimal("50")))
    assert first.needs_confirmation

    reply = apply(ledger, Intent(IntentType.UNKNOWN), "aamaa")

    assert not reply.needs_confirmation
    assert "Suresh" in reply.text
    assert "50" in apply(ledger, Intent(IntentType.BALANCE_QUERY, "Suresh")).text


def test_tamil_no_confirmation_discards_pending_entry():
    ledger = make_ledger()
    apply(ledger, Intent(IntentType.ADD_CREDIT, "Suresh", Decimal("50")))

    reply = apply(ledger, Intent(IntentType.UNKNOWN), "இல்லை")

    assert "save pannala" in reply.text
    assert "puriyala" in apply(ledger, Intent(IntentType.BALANCE_QUERY, "Suresh")).text


def test_undo_after_correction_restores_original_entry():
    ledger = make_ledger()
    apply(ledger, Intent(IntentType.ADD_CREDIT, "Ravi", Decimal("205")))
    apply(ledger, Intent(IntentType.CORRECT_AMOUNT, amount=Decimal("250")))

    apply(ledger, Intent(IntentType.UNDO))

    assert "205" in apply(ledger, Intent(IntentType.BALANCE_QUERY, "Ravi")).text


def test_default_repository_can_be_used_from_another_thread(tmp_path):
    repository = LedgerRepository(database_path=tmp_path / "ledger.sqlite3")
    errors = []

    def add_customer():
        try:
            repository.add_customer(__import__("shopease.matching", fromlist=["Customer"]).Customer(1, "Ravi"), "ravi")
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=add_customer)
    thread.start()
    thread.join()

    assert not errors
    assert repository.customers()[0].name == "Ravi"
