# A09 Signoff Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the formal E13 B1 server evidence, explain the A09 handoff hash difference, and publish A09-downloadable return materials from the authorized personal branch.

**Architecture:** Treat `work/server-evidence/e13-b1-server-formal-20261122-195038/` and the existing return archive as immutable source evidence. Derive a concise, tracked delivery record under `evidence/students/241880481/e13-e14/`; because the original archive exceeds GitHub's 100 MiB single-file limit, preserve it and, if byte-exact splitting is viable, publish sub-100-MiB parts plus reconstruction instructions and hashes.

**Tech Stack:** PowerShell, Git, Git bundle, tar/gzip, Python JSON comparison, SHA-256, GitHub raw/blob URLs.

## Global Constraints

- Preserve all old evidence and unrelated worktree changes.
- Expected return archive SHA256 is `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`.
- Verify fix commit `74eff064e1eae3e244b0acf80880c92fb4635e26` and parent `ba688c40d13cd8658e554f7544f1546d35b4b397` from the delivered bundle.
- Preserve source job `job-131c4b1d8c34469aaa31f9e2a9da1736`, trace `trace-c224eaab92394b91bedfc2dea14ebc61`, and incremental-check SHA256 `504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224` unless evidence proves an association error.
- Final status text remains `服务器实测通过，待 A09 核验签收`.
- Push only this task's files to `student/241880481/e13-e14-b1` on `https://github.com/llxxy-cn/devops-b09.git`.

---

### Task 1: Verify server identities and outcomes

**Files:**
- Read: `work/server-evidence/e13-b1-server-formal-20261122-195038/`
- Create: `evidence/students/241880481/e13-e14/A09-SIGNOFF-DELIVERY.md`

**Interfaces:**
- Consumes: C1/C2/C3/recovery request, result, validation, recheck, assertion, identity, and summary files.
- Produces: exact job/trace IDs, Base/Target, MD/RD, rebuild count, rejection/recovery outcomes, artifact paths and SHA256 values.

- [ ] **Step 1:** Parse C1 request/result and assertion files and cross-check job/trace, Base/Target, MD=0, RD=1, and 6/6 rebuild evidence.
- [ ] **Step 2:** Calculate SHA256 for the authoritative C1 `candidate.patch`, `validation/validation.json`, and final `validation/recheck.json`, retaining their full repository-relative paths.
- [ ] **Step 3:** Read C2/C3/recovery results and assertions and record rejection codes, patch-absence checks, and successful recovery identity.
- [ ] **Step 4:** Extract the delivered Git bundle to a temporary directory, verify the fix commit, its parent, and the bundle's integrity, then remove only that temporary extraction.

### Task 2: Trace the handoff hash difference

**Files:**
- Read: `work/server-evidence/e13-b1-server-formal-20261122-195038/inputs/request-c1.json`
- Read: `work/server-evidence/e13-b1-server-formal-20261122-195038/c1/run/fixed-md-input.json`
- Read: `work/server-evidence/e13-b1-server-formal-20261122-195038/inputs/fixed-md-a09.json`
- Read: A09 original report located from repository history or the return archive
- Modify: `evidence/students/241880481/e13-e14/A09-SIGNOFF-DELIVERY.md`

**Interfaces:**
- Consumes: request URI/SHA fields, handoff-generation logs/code, actual consumed input, and A09 original bytes.
- Produces: byte hashes, normalized business-data comparison, `source_report` comparison, and a root-cause conclusion.

- [ ] **Step 1:** Trace the request path through `handoff_a_to_b.py` and the server logs to identify the exact consumed file and recorded hash.
- [ ] **Step 2:** Hash all candidate JSON files and compare raw bytes, encodings/newlines, JSON key ordering/formatting, business fields, and `source_report` fields.
- [ ] **Step 3:** Test the hypothesis that envelope regeneration/serialization alone caused the byte-hash difference; if association fields differ, stop and repair only after a failing reproducible check.
- [ ] **Step 4:** Document whether the two hashes identify an original report versus a regenerated envelope, including preserved job/trace/incremental hash values.

### Task 3: Prepare repository-safe delivery files

**Files:**
- Create: `evidence/students/241880481/e13-e14/a09-e13-b09-server-return-20261122-195038.tar.gz.part01`
- Create: `evidence/students/241880481/e13-e14/a09-e13-b09-server-return-20261122-195038.tar.gz.part02`
- Create: `evidence/students/241880481/e13-e14/a09-e13-b09-server-return-20261122-195038.tar.gz.part03`
- Create: `evidence/students/241880481/e13-e14/a09-e13-b09-server-return-20261122-195038.tar.gz.part04`
- Create: `evidence/students/241880481/e13-e14/SHA256SUMS`
- Modify: `evidence/students/241880481/e13-e14/A09-SIGNOFF-DELIVERY.md`

**Interfaces:**
- Consumes: immutable 154,556,278-byte archive.
- Produces: four byte-exact reconstructable parts below GitHub's 50 MiB warning threshold, part hashes, reconstructed archive hash, and PowerShell/POSIX reconstruction commands.

- [ ] **Step 1:** Split the original archive at a fixed byte boundary so every tracked part is below GitHub's 100 MiB limit, without modifying the original archive.
- [ ] **Step 2:** Reconstruct the archive in a temporary directory and verify byte length and SHA256 equal the original.
- [ ] **Step 3:** Generate `SHA256SUMS` covering the delivery note and each part, while recording the reconstructed archive's expected SHA256 in the note.
- [ ] **Step 4:** Run `git diff --check`, inspect staged paths and sizes, and ensure the unrelated pre-existing plan remains unstaged.

### Task 4: Commit, push, and verify remote bytes

**Files:**
- Commit only: `docs/superpowers/plans/2026-11-23-a09-signoff-delivery.md`
- Commit only: `evidence/students/241880481/e13-e14/`

**Interfaces:**
- Consumes: verified local delivery tree.
- Produces: immutable commit SHA, pushed personal branch, raw download links pinned to that SHA, and remote-vs-local byte verification.

- [ ] **Step 1:** Run the applicable repository test suite plus artifact-specific reconstruction/hash verification immediately before committing.
- [ ] **Step 2:** Stage only the listed plan and delivery directory, review `git diff --cached --stat` and `git diff --cached`, then commit with a task-specific message.
- [ ] **Step 3:** Push `student/241880481/e13-e14-b1` to `origin` without force.
- [ ] **Step 4:** Fetch raw URLs pinned to the full commit SHA, hash downloaded part bytes, reconstruct the archive, and confirm the remote result equals `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`.
- [ ] **Step 5:** Provide a ready-to-send A09 reply containing links, hashes, identities, commit ancestry, handoff conclusion, and status `服务器实测通过，待 A09 核验签收`.
