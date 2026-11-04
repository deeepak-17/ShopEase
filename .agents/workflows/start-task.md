---
description: Start a GitHub issue: sync main, branch, plan, then test-first build
---

1. Ask the human for the issue number if not given. Read it with `gh issue view <n>` (or ask them to paste it).
2. Sync: `git switch main && git pull --rebase origin main`.
3. Create the branch: `git switch -c b/<short-name>`.
4. Assign the issue: `gh issue edit <n> --add-assignee @me`.
5. Read `AGENTS.md` and `src/shopease/contracts.py`. Confirm the task stays inside Member B's folders.
6. Write a short plan (files to touch, tests to write) as a task artifact and wait for approval.
7. Write failing tests in `tests/<module>/`, run `pytest`, and confirm they fail.
8. Implement until `pytest` passes, then tidy the code.
9. Commit with a conventional message (`feat: ...`). No AI attribution.
