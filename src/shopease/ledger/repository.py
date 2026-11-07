"""SQLite persistence for the append-only udhaar ledger."""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
import os
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Callable, Iterable

from shopease.matching import Customer


PAISE = Decimal("100")


def to_paise(amount: Decimal) -> int:
    value = (amount * PAISE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if value <= 0:
        raise ValueError("amount must be positive")
    return int(value)


def from_paise(amount: int) -> Decimal:
    return Decimal(amount) / PAISE


class LedgerRepository:
    """Owns SQL and leaves ledger business decisions to the service."""

    def __init__(
        self,
        connection: sqlite3.Connection | None = None,
        now: Callable[[], datetime] | None = None,
        database_path: str | Path | None = None,
    ) -> None:
        self._lock = RLock()
        if connection is not None:
            self.connection = connection
        else:
            path = database_path or os.environ.get("SHOPEASE_DB_PATH", "shopease.db")
            self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_key TEXT NOT NULL,
                credit_limit_paise INTEGER
            );
            CREATE TABLE IF NOT EXISTS aliases (
                alias_key TEXT PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id)
            );
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                kind TEXT NOT NULL CHECK (kind IN ('credit', 'payment', 'sale')),
                amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
                items TEXT,
                transcript TEXT NOT NULL,
                audio_path TEXT,
                created_at TEXT NOT NULL,
                replaces_id INTEGER REFERENCES entries(id),
                voided INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        self.connection.commit()

    def add_customer(self, customer: Customer, name_key: str, credit_limit: Decimal | None = None) -> None:
        limit = None if credit_limit is None else to_paise(credit_limit)
        self.connection.execute(
            "INSERT INTO customers (id, name, name_key, credit_limit_paise) VALUES (?, ?, ?, ?)",
            (customer.id, customer.name, name_key, limit),
        )
        self.connection.commit()

    def customers(self) -> tuple[Customer, ...]:
        rows = self.connection.execute("SELECT id, name FROM customers ORDER BY id").fetchall()
        return tuple(Customer(int(row["id"]), str(row["name"])) for row in rows)

    def aliases(self) -> dict[str, int]:
        rows = self.connection.execute("SELECT alias_key, customer_id FROM aliases").fetchall()
        return {str(row["alias_key"]): int(row["customer_id"]) for row in rows}

    def add_alias(self, alias_key: str, customer_id: int) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO aliases (alias_key, customer_id) VALUES (?, ?)",
            (alias_key, customer_id),
        )
        self.connection.commit()

    def insert_entry(
        self,
        customer_id: int | None,
        kind: str,
        amount: Decimal,
        items: Iterable[object],
        transcript: str,
        *,
        created_at: datetime | None = None,
        replaces_id: int | None = None,
    ) -> int:
        timestamp = (created_at or self.now()).isoformat()
        cursor = self.connection.execute(
            """
            INSERT INTO entries
            (customer_id, kind, amount_paise, items, transcript, created_at, replaces_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id, kind, to_paise(amount), json.dumps(tuple(items)),
                transcript, timestamp, replaces_id,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def active_entries(self, customer_id: int | None = None) -> list[sqlite3.Row]:
        query = """
            SELECT * FROM entries
            WHERE voided = 0
              AND id NOT IN (
                  SELECT replaces_id FROM entries
                  WHERE replaces_id IS NOT NULL AND voided = 0
              )
        """
        parameters: tuple[object, ...] = ()
        if customer_id is not None:
            query += " AND customer_id = ?"
            parameters = (customer_id,)
        query += " ORDER BY id"
        return self.connection.execute(query, parameters).fetchall()

    def latest_active(self, customer_id: int | None = None) -> sqlite3.Row | None:
        entries = self.active_entries(customer_id)
        return entries[-1] if entries else None

    def void_entry(self, entry_id: int) -> None:
        with self._lock:
            self.connection.execute("UPDATE entries SET voided = 1 WHERE id = ?", (entry_id,))
            self.connection.commit()

    def balance(self, customer_id: int) -> Decimal:
        total = Decimal("0")
        for row in self.active_entries(customer_id):
            amount = from_paise(int(row["amount_paise"]))
            total += amount if row["kind"] == "credit" else -amount
        return total

    def history(self, customer_id: int) -> tuple[Decimal, ...]:
        return tuple(
            from_paise(int(row["amount_paise"]))
            for row in self.active_entries(customer_id)
            if row["kind"] == "credit"
        )

    def daily_total(self, day: date) -> Decimal:
        prefix = day.isoformat()
        row = self.connection.execute(
            """
            SELECT COALESCE(SUM(amount_paise), 0) AS total FROM entries
            WHERE created_at LIKE ? AND voided = 0
              AND id NOT IN (
                  SELECT replaces_id FROM entries
                  WHERE replaces_id IS NOT NULL AND voided = 0
              )
              AND kind IN ('credit', 'sale')
            """,
            (prefix + "%",),
        ).fetchone()
        return from_paise(int(row["total"]))

    def aging(self, before: datetime, minimum_days: int) -> tuple[Customer, ...]:
        cutoff = before.timestamp() - minimum_days * 86400
        customers: list[Customer] = []
        for customer in self.customers():
            old_credit = any(
                row["kind"] == "credit"
                and datetime.fromisoformat(str(row["created_at"])).timestamp() <= cutoff
                for row in self.active_entries(customer.id)
            )
            if old_credit and self.balance(customer.id) > 0:
                customers.append(customer)
        return tuple(customers)
