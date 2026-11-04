---
description: Check the branch and open a pull request for review by Member A
---

1. Run `pytest`. Stop if anything fails.
2. Run `git diff --name-only origin/main...HEAD`. If any file is outside Member B's folders, list it and ask the human before going on.
3. Rebase on the latest main: `git fetch origin && git rebase origin/main`, then run `pytest` again.
4. Push: `git push -u origin HEAD`.
5. Open the PR: `gh pr create --fill --body "Closes #<issue>"`, filling in the PR template checklist. No AI attribution in the title or body.
6. Give the human the PR link.
