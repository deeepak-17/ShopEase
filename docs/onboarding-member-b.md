# Member B: getting started with Antigravity

About 15 minutes from zero to your first task.

## 1. One-time setup

1. Accept the GitHub collaborator invite (check your email or github.com/notifications).
2. Clone and open the folder in Antigravity:
   ```bash
   git clone git@github.com:deeepak-17/ShopEase.git
   cd ShopEase
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env      # paste your GNANI_API_KEY from https://app.gnani.ai/voice
   pytest                    # should pass
   ```
3. Install the GitHub CLI and log in (`gh auth login`). The workflows use it to
   read issues and open PRs.

## 2. What Antigravity already knows

The repo is set up so the agent picks up the context on its own:

- `AGENTS.md`: what ShopEase is, who owns which folder, the contract,
  the Prisma test results, and coding rules.
- `.agents/rules/member-b-scope.md` (always on): keeps the agent inside your
  folders, asks before touching shared files, plans before coding, tests first.
- `.agents/workflows/`: slash commands in the agent chat:
  - `/start-task`: syncs main, creates your branch, plans, builds test-first
  - `/open-pr`: checks tests and changed files, pushes, opens the PR
  - `/sync`: pulls main, flags contract changes, shows both members' progress

## 3. Your issues

Filter the issues by the `owner: B` label. Suggested order:

1. **Agree `contracts.py`** with Deepak (shared). Read `src/shopease/contracts.py`
   and `docs/interfaces.md`. Say what the ledger needs that's missing.
2. Ledger on SQLite (implements `contracts.Ledger`)
3. Phonetic name matching (Tamil and Latin script)
4. Smart confirmation
5. Timbre Tamil replies
6. Live dashboard

## 4. Starter prompts

Paste these into the agent chat:

- `/start-task 6`, then: "Build the SQLite ledger that implements
  `contracts.Ledger`. Test with hand-built `ParseResult` objects only."
- "Read AGENTS.md and contracts.py, then tell me what my ledger receives and
  must return, with one example for each `IntentType`."
- "Design phonetic matching so `Ravi`, `ரவி` and `Ravi அண்ணா` all match the
  customer Ravi Kumar, and two close matches give a question back. Plan first."

## 5. Tips for Antigravity here

- Use **Planning** mode for new modules and review the plan before approving.
  Use **Fast** mode for small fixes.
- Review the agent's diff before every commit, and check that it only touches your folders.
- One conversation per issue keeps the context clean.
- Run `/sync` each morning before starting.
