"""Ledger application service implementing the shared contract."""

from datetime import date
from decimal import Decimal
import logging

from shopease.confirmation import decide
from shopease.contracts import Intent, IntentType, Ledger, ParseResult, Reply
from shopease.matching import Ambiguous, Matched, NoMatch, Customer, match_name, normalise_name, phonetic_key

from .repository import LedgerRepository

LOGGER = logging.getLogger(__name__)


class SQLiteLedger(Ledger):
    """Apply parser intents in order and persist append-only entries."""

    def __init__(self, repository: LedgerRepository | None = None) -> None:
        self.repository = repository or LedgerRepository()

    def apply(self, result: ParseResult) -> Reply:
        if result.is_ambiguous:
            return Reply("Idhu sariyaa puriyala. Marubadi sollunga.", True)
        if not result.intents:
            return Reply("Enna seiyanum-nu sollunga.", True)
        replies: list[str] = []
        for intent in result.intents:
            reply = self._apply_intent(intent, result)
            replies.append(reply.text)
            if reply.needs_confirmation:
                return reply
        return Reply(" ".join(replies))

    def _apply_intent(self, intent: Intent, result: ParseResult) -> Reply:
        if intent.type == IntentType.TEACH_ALIAS:
            return self._teach_alias(intent)
        if intent.type == IntentType.UNKNOWN:
            return Reply("Idha seiya mudiyala. Marubadi sollunga.", True)
        if intent.type == IntentType.UNDO:
            return self._undo(result.transcript)
        if intent.type == IntentType.CORRECT_AMOUNT:
            return self._correct(intent, result.transcript)
        if intent.type == IntentType.DAILY_TOTAL:
            return self._daily_total()
        if intent.type == IntentType.BALANCE_QUERY:
            return self._balance(intent)
        return self._money_intent(intent, result)

    def _resolve(self, spoken_name: str | None) -> Matched | Ambiguous | NoMatch:
        if not spoken_name:
            return NoMatch("")
        return match_name(spoken_name, self.repository.customers(), self.repository.aliases())

    def _money_intent(self, intent: Intent, result: ParseResult) -> Reply:
        if intent.amount is None:
            return Reply("Thogai sollunga.", True)
        match = self._resolve(intent.spoken_name)
        decision = decide(name_match=match, amount=intent.amount, history=(
            self.repository.history(match.customer.id) if isinstance(match, Matched) else ()
        ))
        if decision.needs_confirmation:
            return Reply(self._confirmation_text(intent, match), True)
        if not isinstance(match, Matched):
            return Reply("Customer peyar puriyala.", True)
        kind = "payment" if intent.type == IntentType.RECORD_PAYMENT else "credit"
        self.repository.insert_entry(match.customer.id, kind, intent.amount, intent.items, result.transcript)
        balance = self.repository.balance(match.customer.id)
        action = "kuduthuttaanga" if kind == "payment" else "add pannitten"
        return Reply(f"{match.customer.name} ku {intent.amount} {action}. Total {balance}.")

    def _confirmation_text(self, intent: Intent, match: object) -> str:
        if isinstance(match, Ambiguous):
            names = ", ".join(candidate.name for candidate in match.candidates)
            return f"{names}-la yaarukku?"
        name = intent.spoken_name or "pudhu customer"
        return f"Pudhu customer {name}-a? {intent.amount} add pannavaa?"

    def _balance(self, intent: Intent) -> Reply:
        match = self._resolve(intent.spoken_name)
        if not isinstance(match, Matched):
            return Reply("Customer peyar puriyala.", True)
        return Reply(f"{match.customer.name} balance {self.repository.balance(match.customer.id)}.")

    def _correct(self, intent: Intent, transcript: str) -> Reply:
        match = self._resolve(intent.spoken_name)
        target = self.repository.latest_active(match.customer.id) if isinstance(match, Matched) else self.repository.latest_active()
        if target is None or intent.amount is None:
            return Reply("Correct panna entry kidaikkala.", True)
        self.repository.insert_entry(
            int(target["customer_id"]), str(target["kind"]), intent.amount, (), transcript,
            replaces_id=int(target["id"]),
        )
        return Reply(f"Thogai {intent.amount} aa correct pannitten.")

    def _undo(self, transcript: str) -> Reply:
        target = self.repository.latest_active()
        if target is None:
            return Reply("Cancel panna entry illa.")
        self.repository.void_entry(int(target["id"]))
        return Reply("Last entry cancel pannitten.")

    def _daily_total(self) -> Reply:
        total = self.repository.daily_total(self.repository.now().date())
        return Reply(f"Inniku vyaapaaram {total}.")

    def _teach_alias(self, intent: Intent) -> Reply:
        if not intent.spoken_name or not intent.alias_target:
            return Reply("Alias-ku rendu peyar sollunga.", True)
        match = self._resolve(intent.alias_target)
        if not isinstance(match, Matched):
            return Reply("Alias target kidaikkala.", True)
        self.repository.add_alias(phonetic_key(intent.spoken_name), match.customer.id)
        return Reply(f"{intent.spoken_name} na {match.customer.name}-nu save pannitten.")

    def add_customer(self, name: str, customer_id: int, credit_limit: Decimal | None = None) -> Customer:
        customer = Customer(customer_id, name)
        self.repository.add_customer(customer, normalise_name(name), credit_limit)
        return customer

    def aging(self, minimum_days: int) -> tuple[Customer, ...]:
        return self.repository.aging(self.repository.now(), minimum_days)
