# Working together

Two people, one repo, no conflicts. The rules below keep it that way.

## 1. Stay in your folders

Each folder has one owner (table in the [README](README.md)). Edit only your
own folders. If you need something changed in your teammate's folder, open an
issue or ask; don't edit it yourself.

**Shared files** (`contracts.py`, `api/`, `pyproject.toml`, `eval/`, docs):
change them only in a small PR of their own that the other person approves.

## 2. Agree the contract first, then build in parallel

`src/shopease/contracts.py` is the handshake: A produces `ParseResult`, B
consumes it and returns a `Reply`. Until B's ledger exists, A tests against a
fake `Ledger`. Until A's parser exists, B tests with hand-built `ParseResult`
objects. Neither side waits for the other.

## 3. Branches and PRs

- Never push to `main` directly. Branch from up-to-date `main`:
  `git switch main && git pull && git switch -c a/parser-numbers`
- Branch prefix: `a/` for Member A, `b/` for Member B, `shared/` for shared files.
- Keep PRs small (one feature). Write tests first.
- Open a PR, link its issue (`Closes #12`), and get the other person's review
  before merging. CI (pytest) must pass.
- Pull `main` at least once a day: `git pull --rebase origin main`.

Commit messages: `feat: ...`, `fix: ...`, `test: ...`, `docs: ...`, `chore: ...`.

## 4. Tracking progress

- Every piece of work is a GitHub **issue**, labelled `owner: A`, `owner: B`
  or `shared`, in a milestone (Must, Should, Launch).
- Assign yourself when you start it. The open PR shows work in progress;
  a closed issue means done.
- See each other's status at any time on the
  [issues page](../../issues) or the project board.
- Blocked on the other person? Comment on the issue and add the `blocked` label.

## 5. Daily sync (5 minutes)

What I finished, what I'm doing next, anything blocked. Also check whether
`contracts.py` needs a change.
