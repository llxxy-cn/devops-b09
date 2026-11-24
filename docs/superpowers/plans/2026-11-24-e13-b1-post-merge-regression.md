# E13 B1 Post-Merge Regression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-run B1 C1-C3 against the merged E13 code baseline, preserve the earlier A09-signed package unchanged, and publish additive post-merge evidence for the final E13 gate.

**Architecture:** Treat `main=298ff1366cdd2f4314cce625492fa813f484893f` as the runtime code baseline and keep the signed `cbf90cce...` delivery immutable. Fast-forward the B1 branch to the merge commit, create a self-contained Git bundle plus the already-fixed A09 material archive, run the existing server harness in a fresh directory, then commit only a compact evidence index and hashes while retaining the full package on the course server.

**Tech Stack:** Git/Git bundle, Bash, Python 3 unittest, Docker, SHA-256, GitHub pull requests.

## Global Constraints

- Do not modify or repack `a09-e13-b09-server-return-20261122-195038.tar.gz` or its four committed parts.
- Preserve A09 signoff date `2026-11-23`, delivery commit `cbf90cce6fcb4950c6326704bd970f9ed80693bb`, and signed archive SHA256 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`.
- Record the tested runtime baseline exactly as `298ff1366cdd2f4314cce625492fa813f484893f`.
- Run C1, C2, C3, and recovery in a new `work/e13-b1-server-formal-*` directory; never overwrite earlier evidence.
- C2 must finish as `STALE_REPORT` without a patch or candidate; C3 must finish as `ARTIFACT_HASH_MISMATCH` without a patch or candidate.
- Do not create `v0.9-rc` or merge the evidence PR as part of this plan.

---

### Task 1: Synchronize and verify the merged baseline

**Files:**
- Preserve: `docs/superpowers/plans/2026-11-17-e13-e14-b1-preflight.md` (untracked user file)
- Create: `docs/superpowers/plans/2026-11-24-e13-b1-post-merge-regression.md`

**Interfaces:**
- Consumes: `origin/main` at merge commit `298ff1366cdd2f4314cce625492fa813f484893f`.
- Produces: B1 branch fast-forwarded to the exact merged tree with no tracked local changes.

- [x] **Step 1: Confirm linked-worktree isolation and branch identity**

Run `git rev-parse --git-dir`, `git rev-parse --git-common-dir`, and `git branch --show-current`; require a linked worktree on `student/241880481/e13-e14-b1`.

- [x] **Step 2: Fetch and fast-forward**

Run `git fetch origin main student/241880481/e13-e14-b1` followed by `git merge --ff-only origin/main`. Confirm `git rev-parse HEAD` equals `298ff1366cdd2f4314cce625492fa813f484893f`.

- [x] **Step 3: Run the merged baseline tests**

Run `python -m unittest discover -s labs/e11e12 -p test_*.py -v`, Linux `python3 -m unittest discover -s labs/e13e14/tests -p 'test_*.py' -v`, Compose configuration with `E14_ROOT` and `E14_IMAGE`, and `python -X utf8 scripts/secret_scan.py . --history`.

### Task 2: Build and verify the server transfer inputs

**Files:**
- Create (ignored): `work/e13-b1-post-merge-298ff13/b09-e13-b1-post-merge.bundle`
- Reuse (ignored): `work/e13-b1-formal-20261122-121914/deliverables/e13-a09-fixed-materials.tar.gz`
- Create (ignored): `work/e13-b1-post-merge-298ff13/SHA256SUMS`

**Interfaces:**
- Consumes: merged B1 Git history and the fixed A09 material archive.
- Produces: two independently hash-verified files that can recreate the exact run on the course server.

- [x] **Step 1: Create a Git bundle containing the merged baseline**

Run `git bundle create work/e13-b1-post-merge-298ff13/b09-e13-b1-post-merge.bundle origin/main student/241880481/e13-e14-b1` and verify it with `git bundle verify`.

- [x] **Step 2: Verify the fixed material archive before transfer**

Run SHA-256 over `work/e13-b1-formal-20261122-121914/deliverables/e13-a09-fixed-materials.tar.gz`, list its members, and verify it contains both `exchange-a09-to-b09/` and `exchange-b09-to-a09/` plus the offline base and candidate files.

- [x] **Step 3: Generate the LF transfer manifest**

Write the two exact file hashes and byte counts into `work/e13-b1-post-merge-298ff13/SHA256SUMS`; verify the manifest under Linux with `sha256sum -c`.

### Task 3: Execute C1-C3 on the course server

**Files:**
- Create on server: `/root/devops-b09-e13-b1-post-merge/`
- Create on server: `/root/devops-b09-e13-b1-post-merge/work/e13-b1-server-formal-<timestamp>/`

**Interfaces:**
- Consumes: the Git bundle, fixed material archive, and an operator-provided reachable SSH target for the course server.
- Produces: fresh C1/C2/C3/recovery job IDs, trace IDs, patch, recheck hashes, context log, and `FAILURES=0` assertions.

- [x] **Step 1: Obtain the exact reachable SSH target**

If no SSH host is configured locally, stop external execution and request the single value needed for `root@<course-server-host>`; do not guess an address or inspect shell history for credentials.

- [x] **Step 2: Transfer and reconstruct the repository**

Copy both Task 2 files, clone the bundle to `/root/devops-b09-e13-b1-post-merge`, check out `298ff1366cdd2f4314cce625492fa813f484893f` in detached mode, and record `git rev-parse HEAD` before running anything.

- [x] **Step 3: Extract materials and run the existing harness**

Extract the fixed archive below `work/e13-a09-fixed-materials`, load the offline image, and run `bash docs/students/241880481/e13-e14/run-server-formal-c1-c3.sh work/e13-a09-fixed-materials`.

- [x] **Step 4: Verify the server result before download**

Require harness exit 0, `FAILURES=0`, C1 and recovery `SUCCEEDED`, C1 six rebuilt/output-matching edges, final MD=0/RD=1, C2 `STALE_REPORT`, C3 `ARTIFACT_HASH_MISMATCH`, and no C2/C3 patch or candidate directory.

- [x] **Step 5: Package without altering raw evidence**

Create a new tar archive from the timestamped evidence directory, generate a separate LF SHA256 manifest, and leave both files under `/root/devops-submissions/241880481/`.

### Task 4: Publish additive evidence and handoff

**Files:**
- Create: `docs/students/241880481/e13-e14/POST-MERGE-REGRESSION-20261124.md`
- Modify: `docs/students/241880481/e13-e14/README.md`
- Modify: `docs/students/241880481/e13-e14/evidence-manifest.sha256`

**Interfaces:**
- Consumes: verified server evidence package and manifest.
- Produces: a stable repository index for B3's final gate and an A09 follow-up message that does not replace the 2026-11-23 signoff.

- [x] **Step 1: Record exact post-merge identities**

Document runtime baseline `298ff136...`, evidence package SHA256/bytes/server path, all new job/trace IDs, C1 repair commit and target parent, C2/C3 rejection facts, and recovery job/trace.

- [x] **Step 2: Link rather than duplicate evidence**

Add repository-relative links to the existing A09 signoff and erratum, and state explicitly that the post-merge package supplements rather than replaces the signed archive.

- [x] **Step 3: Add B3 and A09 handoff text**

Provide B3 with the final-gate row values and ask A09 whether the new post-merge regression requires any additional verification; do not claim a second signoff unless A09 actually supplies one.

- [x] **Step 4: Run final verification**

Run relevant unittests, `bash -n` on the server harness, `git diff --check`, manifest verification, secret scan, and verify every stated hash/job/trace against the downloaded evidence.

- [ ] **Step 5: Commit, push, and create the evidence PR**

Commit only the plan and additive evidence/docs, push `student/241880481/e13-e14-b1`, and open a PR to `main` titled `E13 B1: record post-merge C1-C3 regression`. Leave merging to group review.
