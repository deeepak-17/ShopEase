"""Shared contract between Member A and Member B.

DRAFT: both members agree on this file before building against it.
Change it only through a PR that both members approve (see CONTRIBUTING.md).

Flow: Prisma transcript -> parser (A) -> ParseResult -> ledger and replies (B).
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


class IntentType(StrEnum):
    ADD_CREDIT = "add_credit"            # "Ravi anna ku 250 kadan"
    RECORD_PAYMENT = "record_payment"    # "Ravi 100 kuduthaar"
    BALANCE_QUERY = "balance_query"      # "Ravi ku evlo baaki?"
    CORRECT_AMOUNT = "correct_amount"    # "205 illa 250"
    UNDO = "undo"                        # "adha cancel pannu"
    DAILY_TOTAL = "daily_total"          # "inniku evlo vyaapaaram"
    SEND_REMINDER = "send_reminder"      # "Ravi ku reminder anuppu"
    TEACH_ALIAS = "teach_alias"          # "Kutty na Karthik"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Item:
    name: str
    quantity: Decimal | None = None
    unit: str | None = None


@dataclass(frozen=True)
class Intent:
    """One ledger action the parser found in a sentence.

    `spoken_name` is the name as heard, honorific stripped, in Tamil or Latin
    script. Member B's name matching resolves it to a customer.
    """

    type: IntentType
    spoken_name: str | None = None
    amount: Decimal | None = None
    items: tuple[Item, ...] = ()
    alias_target: str | None = None


@dataclass(frozen=True)
class ParseResult:
    transcript: str
    intents: tuple[Intent, ...] = field(default_factory=tuple)
    is_ambiguous: bool = False


@dataclass(frozen=True)
class Reply:
    """What the shopkeeper sees and hears after a command."""

    text: str
    needs_confirmation: bool = False
    audio_url: str | None = None


class Ledger(Protocol):
    """Implemented by Member B. Member A tests against a fake."""

    def apply(self, result: ParseResult) -> Reply: ...
