---
description: Daily sync: pull main, flag contract changes, show both members' progress
---

1. `git fetch origin` and `git log --oneline HEAD..origin/main` to show what landed since the last sync.
2. If `src/shopease/contracts.py` changed (`git diff HEAD origin/main -- src/shopease/contracts.py`), summarise the change and which Member B code it affects.
3. Update: `git switch main && git pull --rebase origin main`. If a feature branch is in progress, rebase it on main and run `pytest`.
4. Show progress:
   - `gh issue list --label "owner: B" --state all`
   - `gh issue list --label "owner: A" --state all`
   - `gh pr list`
5. Summarise in three lines: done, in progress, blocked (issues labelled `blocked`).
