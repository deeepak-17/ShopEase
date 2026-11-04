# Interfaces between A and B

Status: **draft**. Both members agree on this, then mark it agreed.

The code version is [`src/shopease/contracts.py`](../src/shopease/contracts.py).
If this page and the code disagree, the code wins. Fix this page.

## Handoff: parser (A) → ledger (B)

A's parser returns a `ParseResult`:

- `transcript`: the Prisma text, punctuation stripped.
- `intents`: one `Intent` per action in the sentence (a sentence can hold several).
- `is_ambiguous`: true when the parser had to guess.

Each `Intent` has a `type`, and when present a `spoken_name` (honorific
stripped, Tamil **or** Latin script, as Prisma returned it), an `amount`
(`Decimal`, rupees), `items`, and an `alias_target` for "Kutty na Karthik".

B's `Ledger.apply(result)` resolves names, decides whether to confirm, writes
the entry and returns a `Reply` (text, `needs_confirmation`, optional Timbre
audio URL).

## Facts from the Prisma test that affect B

- Prisma returns **no confidence score**, so confirmation must use other
  signals: unknown name, unusual amount, `is_ambiguous`.
- Names come back in either script (`Ravi அண்ணாவுக்கு` or `ரவிக்கு`), so
  matching must accept both.

## HTTP (shared, `api/`)

To agree: `POST /command` (audio in, `Reply` out), and `GET /ledger` for the
dashboard.
