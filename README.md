# ShopEase

A Tanglish voice ledger for small shops in Tamil Nadu. The shopkeeper presses a
button and speaks ("Ravi anna ku 250 kadan"). Gnani Prisma transcribes, our
parser turns the words into ledger actions, and Gnani Timbre confirms aloud in
Tamil.

Entry for Gnani AI's Great Indian AI Internship Challenge. Full spec:
[docs/spec.pdf](docs/spec.pdf) (written under the project's old name, KadaiMate).

## How it fits together

```
phone mic ─▶ stt (Prisma) ─▶ parser ─▶ ParseResult ─▶ matching ─▶ confirmation ─▶ ledger ─▶ tts (Timbre)
 web/talk        A             A       contracts.py       B            B             B          B
                                         SHARED                                          web/dashboard (B)
```

The one place A and B meet in code is
[`src/shopease/contracts.py`](src/shopease/contracts.py). See
[docs/interfaces.md](docs/interfaces.md).

## Layout and owners

| Path | What | Owner |
|---|---|---|
| `src/shopease/contracts.py` | Intent schema and Ledger interface | Shared |
| `src/shopease/api/` | FastAPI routes wiring the pipeline | Shared |
| `src/shopease/stt/` | Prisma speech to text | A (Deepak) |
| `src/shopease/parser/` | Tanglish parser | A (Deepak) |
| `web/talk/` | Push-to-talk screen | A (Deepak) |
| `src/shopease/matching/` | Phonetic names, aliases | B |
| `src/shopease/confirmation/` | Smart confirmation | B |
| `src/shopease/ledger/` | SQLite ledger | B |
| `src/shopease/tts/` | Timbre replies and reminders | B |
| `web/dashboard/` | Live dashboard | B |
| `tests/<module>/` | Tests, mirroring `src/` | Owner of the module |
| `eval/` | Accuracy test set and results table | Shared |
| `spikes/` | Throwaway API tests (Prisma, Timbre) | A |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add your GNANI_API_KEY
pytest
```

Never commit `.env` or voice recordings (`clips/`). Both are git-ignored.

## Working together

See [CONTRIBUTING.md](CONTRIBUTING.md) for branches, PRs and how we track
progress.
