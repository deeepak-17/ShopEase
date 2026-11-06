from datetime import datetime, timezone
from decimal import Decimal
import sqlite3

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
