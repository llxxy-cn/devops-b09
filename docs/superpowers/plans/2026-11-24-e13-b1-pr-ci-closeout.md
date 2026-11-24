# E13 B1 PR and CI Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure `student/241880481/e13-e14-b1` has an accurate PR to `main`, verify remote CI, and leave the PR ready for group review without merging it.

**Architecture:** Treat remote `origin/main` and the GitHub PR API as the source of truth. Build the PR description from the actual merge-base diff and committed evidence, then inspect every check run for the current head; only branch-caused failures may change code, and each fix must be reproduced locally before pushing.

**Tech Stack:** Git, GitHub REST API, PowerShell, Python `unittest`, WSL/Linux, GitHub Actions/GitLab CI metadata.

## Global Constraints

- Head branch is `student/241880481/e13-e14-b1` at starting commit `8b68a71eae5b5acc436b89bd21212e8b988d8e2d`.
- Base branch is `main`.
- Existing PRs are updated; a new PR is created only when no open PR has this head/base pair.
- PR content must cover project adaptation, offline builds, C1-C3 server results, A09 signoff, and commit-pinned evidence links.
- Fix only failures caused by this branch; do not mask unrelated or infrastructure failures.
- Do not merge the PR; leave final integration to group review.
- Preserve unrelated untracked file `docs/superpowers/plans/2026-11-17-e13-e14-b1-preflight.md`.

---

### Task 1: Establish remote PR and main state

**Files:**
- Read: GitHub PR API for `llxxy-cn/devops-b09`
- Read: `origin/main` and `origin/student/241880481/e13-e14-b1`

**Interfaces:**
- Consumes: remote refs, open/closed PR records, current branch head.
- Produces: authoritative PR decision, merge base, commit list, and changed-file inventory.

- [ ] **Step 1:** Fetch `main` and the personal branch without rewriting local commits.
- [ ] **Step 2:** Query open PRs for head `llxxy-cn:student/241880481/e13-e14-b1` and base `main`; also inspect closed PRs to avoid duplicating an already merged line of work.
- [ ] **Step 3:** Run `git log origin/main..HEAD`, `git diff --stat origin/main...HEAD`, and `git diff --name-status origin/main...HEAD` and save the exact results for the PR summary.

### Task 2: Build and publish the PR description

**Files:**
- Read: `docs/students/241880481/e13-e14/README.md`
- Read: `docs/students/241880481/e13-e14/formal/README.md`
- Read: `evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md`
- Read: `evidence/students/241880481/e13-e14/ERRATA-20261123.md`

**Interfaces:**
- Consumes: merge diff and committed evidence.
- Produces: PR title/body with exact outcomes and commit-pinned evidence URLs.

- [ ] **Step 1:** Summarize root-Make compatibility, transfer-hash validation, and the preserved legacy request path from the actual diff.
- [ ] **Step 2:** Summarize the original/derived Dockerfile and offline image mapping, including immutable SHA256 identities.
- [ ] **Step 3:** Summarize C1 success, C2 `STALE_REPORT`, C3 `ARTIFACT_HASH_MISMATCH`, recovery, fixed commit ancestry, and A09's 2026-11-23 signoff.
- [ ] **Step 4:** Update the existing PR through the GitHub API, or create it against `main` when no open PR exists; do not enable auto-merge.

### Task 3: Inspect and repair remote CI

**Files:**
- Read: GitHub check-runs, statuses, Actions runs/jobs/logs for the PR head.
- Modify only if required: the smallest branch-owned file that causes a reproducible failure.
- Test: `labs/e11e12/test_*.py`, `labs/e13e14/tests/test_*.py`, plus the failing CI command.

**Interfaces:**
- Consumes: check conclusions and failing job logs.
- Produces: classified failures and, when branch-caused, a tested minimal fix pushed to the same branch.

- [ ] **Step 1:** Enumerate every check/status for the exact head SHA and read logs for non-success conclusions.
- [ ] **Step 2:** For each failure, distinguish branch regression from base/infrastructure failure using the error, workflow definition, and local reproduction.
- [ ] **Step 3:** If branch-caused, write or identify the minimal failing test, reproduce it, implement one root-cause fix, run focused and full tests, commit, and push.
- [ ] **Step 4:** Wait for the newest head's CI to reach a terminal state and re-read all conclusions.

### Task 4: Final verification and review handoff

**Files:**
- Read: final PR, remote head, check runs, mergeability, review state.

**Interfaces:**
- Consumes: terminal CI and PR metadata.
- Produces: PR URL, CI status, and concrete group-review checklist.

- [ ] **Step 1:** Verify remote head equals local `HEAD`, PR base/head are correct, and the PR body contains all four requested subject areas and evidence links.
- [ ] **Step 2:** Run fresh local E11/E12 and E13 suites plus `git diff --check` before the final status claim.
- [ ] **Step 3:** Report the PR URL, per-check CI state, and review items covering contract compatibility, offline provenance, C1-C3 rejection boundaries, signoff/erratum immutability, and the intentionally unmerged state.
