---
trigger: always_on
---

# Member B working rules

Follow `AGENTS.md` at the repo root. In addition:

- You are working for **Member B**. Write only in:
  `src/shopease/matching/`, `src/shopease/confirmation/`, `src/shopease/ledger/`,
  `src/shopease/tts/`, `web/dashboard/`, and the matching folders under `tests/`.
- Never edit Member A's folders: `src/shopease/stt/`, `src/shopease/parser/`,
  `web/talk/`, `spikes/`. If you need something from them, write a short note
  for the human to post on the GitHub issue.
- If the task needs `src/shopease/contracts.py` or `src/shopease/api/` changed,
  stop and ask before editing. These are shared and need a separate PR.
- Before writing code, show a short plan and wait for approval.
- Write the failing test first, then the code. Run `pytest` before saying a task is done.
- Work on a `b/<short-name>` branch, never on `main`.
