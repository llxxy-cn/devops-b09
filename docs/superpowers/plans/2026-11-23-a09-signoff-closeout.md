# A09 Signoff Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Archive A09's 2026-11-23 signoff, correct the delivery documentation and checksum workflow without changing the signed-off return archive, then commit and push the personal branch.

**Architecture:** Keep commit `cbf90cce6fcb4950c6326704bd970f9ed80693bb` and the 154,556,278-byte return archive immutable. Add a tracked signoff record and erratum beside the split archive, normalize only the external checksum manifest to LF, and document a stream-normalization command for the CRLF manifest already sealed inside the archive.

**Tech Stack:** Markdown, Git, PowerShell, WSL/Linux `sha256sum`, tar/gzip, SHA-256.

## Global Constraints

- Signoff date is `2026-11-23`.
- Delivery commit is `cbf90cce6fcb4950c6326704bd970f9ed80693bb`.
- Signed-off return archive remains byte-for-byte unchanged at SHA256 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`.
- Personal status text becomes `服务器实测通过，A09 已核验签收`.
- Preserve unrelated untracked file `docs/superpowers/plans/2026-11-17-e13-e14-b1-preflight.md`.
- Push only to `student/241880481/e13-e14-b1`, without force.

---

### Task 1: Reproduce and delimit the checksum defect

**Files:**
- Read: `work/e13-b1-formal-20261122-121914/deliverables/a09-e13-b09-server-return-20261122-195038.tar.gz`
- Read: `evidence/students/241880481/e13-e14/SHA256SUMS`

**Interfaces:**
- Consumes: signed-off archive and tracked external manifest.
- Produces: byte-count evidence for CRLF/LF and Linux failure/pass output.

- [x] **Step 1:** Confirm the archive's size and SHA256 against the fixed delivery commit.
- [x] **Step 2:** Extract the archive in a disposable WSL directory and run the packaged `sha256sum -c SHA256SUMS`; record the observed result accurately (GNU `sha256sum` accepted CRLF and all 17 payload files passed).
- [x] **Step 3:** Run `sed 's/\r$//' SHA256SUMS | sha256sum -c -` in the same Linux directory and require all 17 payload files to pass.

### Task 2: Record signoff and erratum

**Files:**
- Create: `evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md`
- Create: `evidence/students/241880481/e13-e14/ERRATA-20261123.md`
- Modify: `evidence/students/241880481/e13-e14/A09-SIGNOFF-DELIVERY.md`

**Interfaces:**
- Consumes: user-relayed A09 signoff wording, fixed commit, archive identity, and source-to-package evidence.
- Produces: immutable signoff record, correction notice, and corrected delivery index.

- [x] **Step 1:** Save the signoff text exactly as relayed, with date, delivery commit, archive name, size, and SHA256.
- [x] **Step 2:** Document that the archive and fixed commit remain unchanged and explain the packaged CRLF checksum-manifest compatibility command.
- [x] **Step 3:** Add a complete table mapping every packaged flat filename to its original server path and verify each SHA256 against `return-manifest.json`.
- [x] **Step 4:** Update the delivery index status and link both the signoff and erratum records.

### Task 3: Update the personal record and normalize the external manifest

**Files:**
- Modify: `docs/students/241880481/e13-e14/README.md`
- Modify: `docs/students/241880481/e13-e14/formal/README.md`
- Modify: `evidence/students/241880481/e13-e14/SHA256SUMS`

**Interfaces:**
- Consumes: completed signoff and erratum records.
- Produces: final personal status, LF-only tracked checksum manifest, and cross-links.

- [x] **Step 1:** Replace pending-signoff wording with `服务器实测通过，A09 已核验签收` and link the records.
- [x] **Step 2:** Keep the tracked checksum manifest as ASCII/LF, enforce `eol=lf`, and normalize both external working-copy manifests without changing the archive.
- [x] **Step 3:** Verify in WSL that the external manifest can check the four present parts and that reconstruction still yields the signed-off archive hash.

### Task 4: Verify, commit, and push

**Files:**
- Commit: the closeout plan and Task 2-3 files only.

**Interfaces:**
- Consumes: final working tree.
- Produces: pushed closeout commit and commit-pinned record links.

- [x] **Step 1:** Run focused Linux checksum checks, archive reconstruction, relevant repository tests, and `git diff --check`.
- [x] **Step 2:** Confirm the archive and four split parts still match their pre-edit SHA256 values.
- [ ] **Step 3:** Stage only intended files, inspect the cached diff, and commit.
- [ ] **Step 4:** Push the personal branch without force and verify the remote branch points to the new commit.
- [ ] **Step 5:** Return the new commit SHA and commit-pinned signoff/erratum links.
