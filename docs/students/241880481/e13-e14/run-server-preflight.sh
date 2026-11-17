#!/usr/bin/env bash
# B09 / 241880481 / E13-E14 server-side preflight.
# Run from the devops-b09 repository root. This script does not push, commit,
# open a PR, or send any external message.

set -uo pipefail

STUDENT_ID="241880481"
BASELINE_COMMIT="80b4dafb836365911e6e85451ee367cc874afa46"
CANDIDATE_BASE="30ffe4c41492334478a2446a8be0662d3f31d478"
CANDIDATE_TARGET="a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293"
A09_URL="https://raw.githubusercontent.com/a-bi-chen/DevOps_1020_Student_Cloud/0cd8054911a18be96900e05c3b7747c6b35a4112/evidence/students/241880375/e11-e12/e11e12-evidence-241880375.tar.gz"
A09_ARCHIVE_SHA="19479d51720decbca2518453e00646a4700c7b21101b018965bfdbc0c8cce648"
A09_REPORT_SHA="8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716"
A09_BASE="3fcb72029bf560afde2d29436395ff3b979a19fd"
A09_TARGET="15c059958a41a5a0513dc048036439843a34ad28"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: run this script inside devops-b09" >&2
  exit 2
}
cd "$REPO_ROOT"

RUN_ID="$(date +%Y%m%d-%H%M%S)"
EVIDENCE_ROOT="$REPO_ROOT/work/e13-b1-server-$RUN_ID"
mkdir -p "$EVIDENCE_ROOT"
SUMMARY="$EVIDENCE_ROOT/summary.tsv"
printf 'step\texit_code\tlog\n' > "$SUMMARY"

run_step() {
  local step="$1"
  shift
  local log="$EVIDENCE_ROOT/$step.log"
  mkdir -p "$(dirname "$log")"
  {
    printf 'START_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'PWD=%s\n' "$PWD"
    printf 'COMMAND='
    printf '%q ' "$@"
    printf '\n'
  } | tee "$log"
  set +e
  "$@" > >(tee -a "$log") 2> >(tee -a "$log" >&2)
  local rc=$?
  set -u
  {
    printf 'EXIT_CODE=%s\n' "$rc"
    printf 'END_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } | tee -a "$log"
  printf '%s\t%s\t%s\n' "$step" "$rc" "$log" >> "$SUMMARY"
  printf '%s\n' "$rc" > "$EVIDENCE_ROOT/$step.exitcode"
  return 0
}

expect_rc() {
  local step="$1" expected="$2"
  local actual
  actual="$(tr -d '\r\n' < "$EVIDENCE_ROOT/$step.exitcode")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'ASSERT_FAIL step=%s expected_rc=%s actual_rc=%s\n' "$step" "$expected" "$actual" | tee -a "$EVIDENCE_ROOT/assertions.log"
    return 1
  fi
  printf 'ASSERT_OK step=%s rc=%s\n' "$step" "$actual" | tee -a "$EVIDENCE_ROOT/assertions.log"
}

FAILURES=0
check_rc() { expect_rc "$1" "$2" || FAILURES=$((FAILURES + 1)); }

echo "EVIDENCE_ROOT=$EVIDENCE_ROOT"

# 0. Record the immutable context before running anything.
run_step context bash -lc '
  set -u
  echo "HOST=$(hostname)"
  uname -a
  echo "GIT_HEAD=$(git rev-parse HEAD)"
  echo "GIT_BRANCH=$(git branch --show-current)"
  git status --short --branch
  git remote -v
  python3 --version
  docker version
'
check_rc context 0
run_step baseline/baseline-object git cat-file -e "$BASELINE_COMMIT^{commit}"
check_rc baseline/baseline-object 0

# 1. B09 fixed sample regression. Build/prepare only when the prerequisites are absent.
if ! docker image inspect "course-e11e12:$STUDENT_ID" >/dev/null 2>&1; then
  run_step baseline/build-image python3 run_e11e12.py build
  check_rc baseline/build-image 0
fi
if [[ ! -f data/integration-sample/e12.json ]]; then
  run_step baseline/prepare-sample python3 run_e11e12.py prepare
  check_rc baseline/prepare-sample 0
fi
mkdir -p "$EVIDENCE_ROOT/baseline"
cp data/integration-sample/e12.json "$EVIDENCE_ROOT/baseline/request-e12.json"
run_step baseline/image-id docker image inspect "course-e11e12:$STUDENT_ID" --format '{{.Id}}'
check_rc baseline/image-id 0
run_step baseline/test python3 run_e11e12.py test
check_rc baseline/test 0
run_step baseline/fixed-sample python3 run_e11e12.py run \
  --request data/integration-sample/e12.json \
  --out "$EVIDENCE_ROOT/baseline/run"
check_rc baseline/fixed-sample 0

# 2. Exchange candidate: isolated worktrees and the three required commands.
mkdir -p "$EVIDENCE_ROOT/candidate"
run_step candidate/add-base git worktree add --detach "$EVIDENCE_ROOT/candidate/base-repo" "$CANDIDATE_BASE"
check_rc candidate/add-base 0
run_step candidate/add-target git worktree add --detach "$EVIDENCE_ROOT/candidate/target-repo" "$CANDIDATE_TARGET"
check_rc candidate/add-target 0
run_step candidate/heads bash -lc "
  echo BASE_HEAD=\$(git -C '$EVIDENCE_ROOT/candidate/base-repo' rev-parse HEAD)
  echo TARGET_HEAD=\$(git -C '$EVIDENCE_ROOT/candidate/target-repo' rev-parse HEAD)
  test \"\$(git -C '$EVIDENCE_ROOT/candidate/base-repo' rev-parse HEAD)\" = '$CANDIDATE_BASE'
  test \"\$(git -C '$EVIDENCE_ROOT/candidate/target-repo' rev-parse HEAD)\" = '$CANDIDATE_TARGET'
"
check_rc candidate/heads 0

for side in base target; do
  project="$EVIDENCE_ROOT/candidate/${side}-repo/fixtures/e11e12-b1-real"
  run_step "candidate/$side-build" bash -lc "cd \"$project\" && make clean && make"
  check_rc "candidate/$side-build" 0
  run_step "candidate/$side-test" bash -lc "cd \"$project\" && make test"
  check_rc "candidate/$side-test" 0
  run_step "candidate/$side-app" bash -lc "cd \"$project\" && ./app"
  check_rc "candidate/$side-app" 0
  if ! grep -Fxq 'hello E3' "$EVIDENCE_ROOT/candidate/${side}-app.log"; then
    echo "ASSERT_FAIL candidate/${side}-app missing exact output: hello E3" | tee -a "$EVIDENCE_ROOT/assertions.log"
    FAILURES=$((FAILURES + 1))
  fi
done

TARGET_PROJECT="$EVIDENCE_ROOT/candidate/target-repo/fixtures/e11e12-b1-real"
run_step candidate/target-dependency-scan bash -lc "
  cd \"$TARGET_PROJECT\"
  PYTHONPATH=\"$REPO_ROOT/labs/e8e10\" python3 -c \"import json; from pathlib import Path; from lab import scan; r=scan(Path('.'), compiler_flags=['-std=c11','-Wall','-Wextra','-Werror']); print(json.dumps(r, indent=2)); assert r['commit']=='$CANDIDATE_TARGET'; assert any(x == {'type':'MISSING','target':'main.o','dependency':'extra.h'} for x in r['findings'])\"
"
check_rc candidate/target-dependency-scan 0

run_step candidate/dockerfile-identity bash -lc "
  set -u
  p=docs/students/241880481/e11-e12/real-project/candidate.Dockerfile
  echo PATH=\"\$p\"
  echo INTRODUCED_COMMIT=\$(git log --diff-filter=A --format=%H -- \"\$p\" | tail -1)
  echo LAST_MODIFIED_COMMIT=\$(git log -1 --format=%H -- \"\$p\")
  echo BLOB=\$(git rev-parse HEAD:\"\$p\")
  sha256sum \"\$p\"
"
check_rc candidate/dockerfile-identity 0

# 3. Download and verify the immutable A09 E12 archive.
ARCHIVE_DIR="$EVIDENCE_ROOT/a09-archive"
ARCHIVE="$ARCHIVE_DIR/e11e12-evidence-241880375.tar.gz"
EXTRACTED="$ARCHIVE_DIR/extracted"
mkdir -p "$ARCHIVE_DIR" "$EXTRACTED"
run_step a09/download curl --fail --location --retry 3 --output "$ARCHIVE" "$A09_URL"
check_rc a09/download 0
run_step a09/archive-hash bash -lc "echo '$A09_ARCHIVE_SHA  $ARCHIVE' | sha256sum --check --strict"
check_rc a09/archive-hash 0
if [[ "$(cat "$EVIDENCE_ROOT/a09/archive-hash.exitcode")" != 0 ]]; then
  echo "Archive hash mismatch; refusing extraction." >&2
  exit 3
fi

run_step a09/extract python3 - "$ARCHIVE" "$EXTRACTED" <<'PY'
import sys, tarfile
from pathlib import Path

archive, out = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
with tarfile.open(archive, "r:gz") as tf:
    for member in tf.getmembers():
        target = (out / member.name).resolve()
        if out != target and out not in target.parents:
            raise SystemExit(f"unsafe archive member: {member.name}")
    tf.extractall(out)
PY
check_rc a09/extract 0

REPORT="$EXTRACTED/work/e11-a-241880375/incremental-check.json"
A09_REPO="$EXTRACTED/data/integration-sample/repo"
A09_CANDIDATE="$EXTRACTED/data/integration-sample/candidate.Dockerfile"
run_step a09/report-identity python3 - "$REPORT" "$A09_REPO" "$A09_REPORT_SHA" "$A09_TARGET" <<'PY'
import hashlib, json, subprocess, sys
from pathlib import Path

report_path, repo_path = Path(sys.argv[1]), Path(sys.argv[2])
expected_hash, expected_target = sys.argv[3], sys.argv[4]
raw = report_path.read_bytes()
actual_hash = hashlib.sha256(raw).hexdigest()
report = json.loads(raw)
repo_head = subprocess.check_output(["git", "-C", str(repo_path), "rev-parse", "HEAD"], text=True).strip()
print(f"REPORT_SHA256={actual_hash}")
print(f"REPORT_KIND={report.get('kind')}")
print(f"REPORT_STATUS={report.get('status')}")
print(f"REPORT_COMMIT={report.get('commit')}")
print(f"REPORT_JOB_ID={report.get('job_id')}")
print(f"REPORT_TRACE_ID={report.get('trace_id')}")
print(f"REPO_HEAD={repo_head}")
assert actual_hash == expected_hash
assert report.get("schema_version") == "e11e12-1"
assert report.get("kind") == "incremental-check"
assert report.get("status") == "SUCCEEDED"
assert report.get("commit") == expected_target
assert report.get("data", {}).get("commit") == expected_target
assert repo_head == expected_target
PY
check_rc a09/report-identity 0

# First consume the unchanged report, then exercise C2 and C3 independently.
VALID_DIR="$EVIDENCE_ROOT/a09-valid"
mkdir -p "$VALID_DIR"
run_step a09/valid-consume python3 labs/e11e12/repair_report.py \
  --project "$A09_REPO" --report "$REPORT" --sha256 "$A09_REPORT_SHA" \
  --kind incremental-check --out "$VALID_DIR/candidate.patch"
check_rc a09/valid-consume 0

C2_DIR="$EVIDENCE_ROOT/c2-stale"
mkdir -p "$C2_DIR"
run_step c2/add-project git -C "$A09_REPO" worktree add --detach "$C2_DIR/project" "$A09_BASE"
check_rc c2/add-project 0
run_step c2/project-head bash -lc "echo C2_PROJECT_HEAD=\$(git -C '$C2_DIR/project' rev-parse HEAD); test \"\$(git -C '$C2_DIR/project' rev-parse HEAD)\" = '$A09_BASE'"
check_rc c2/project-head 0
run_step c2/stale-report python3 labs/e11e12/repair_report.py \
  --project "$C2_DIR/project" --report "$REPORT" --sha256 "$A09_REPORT_SHA" \
  --kind incremental-check --out "$C2_DIR/candidate.patch"
check_rc c2/stale-report 1
if [[ -e "$C2_DIR/candidate.patch" ]]; then
  echo "ASSERT_FAIL C2 generated a patch" | tee -a "$EVIDENCE_ROOT/assertions.log"
  FAILURES=$((FAILURES + 1))
fi
grep -q 'STALE_REPORT' "$EVIDENCE_ROOT/c2/stale-report.log" || {
  echo "ASSERT_FAIL C2 log lacks STALE_REPORT" | tee -a "$EVIDENCE_ROOT/assertions.log"
  FAILURES=$((FAILURES + 1))
}

C3_DIR="$EVIDENCE_ROOT/c3-tampered"
mkdir -p "$C3_DIR"
cp "$REPORT" "$C3_DIR/incremental-check-tampered.json"
printf '\n' >> "$C3_DIR/incremental-check-tampered.json"
run_step c3/hashes bash -lc "sha256sum '$REPORT' '$C3_DIR/incremental-check-tampered.json'"
check_rc c3/hashes 0
run_step c3/hash-mismatch python3 labs/e11e12/repair_report.py \
  --project "$A09_REPO" --report "$C3_DIR/incremental-check-tampered.json" \
  --sha256 "$A09_REPORT_SHA" --kind incremental-check --out "$C3_DIR/candidate.patch"
check_rc c3/hash-mismatch 1
if [[ -e "$C3_DIR/candidate.patch" ]]; then
  echo "ASSERT_FAIL C3 generated a patch" | tee -a "$EVIDENCE_ROOT/assertions.log"
  FAILURES=$((FAILURES + 1))
fi
grep -q 'ARTIFACT_HASH_MISMATCH' "$EVIDENCE_ROOT/c3/hash-mismatch.log" || {
  echo "ASSERT_FAIL C3 log lacks ARTIFACT_HASH_MISMATCH" | tee -a "$EVIDENCE_ROOT/assertions.log"
  FAILURES=$((FAILURES + 1))
}

RESTORED_DIR="$EVIDENCE_ROOT/a09-restored"
mkdir -p "$RESTORED_DIR"
run_step a09/restored-consume python3 labs/e11e12/repair_report.py \
  --project "$A09_REPO" --report "$REPORT" --sha256 "$A09_REPORT_SHA" \
  --kind incremental-check --out "$RESTORED_DIR/candidate.patch"
check_rc a09/restored-consume 0

# Record final hashes and result paths without changing the repository.
run_step final/artifact-hashes bash -lc "
  find '$EVIDENCE_ROOT' -type f \
    \( -name 'result.json' -o -name 'candidate.patch' -o -name '*.log' -o -name '*.exitcode' -o -name 'request-e12.json' \) \
    ! -name 'artifact-hashes.log' \
    -print0 | sort -z | xargs -0 sha256sum
"
check_rc final/artifact-hashes 0

echo "FAILURES=$FAILURES" | tee -a "$EVIDENCE_ROOT/assertions.log"
echo "SUMMARY=$SUMMARY"
echo "EVIDENCE_ROOT=$EVIDENCE_ROOT"
if (( FAILURES != 0 )); then
  exit 1
fi
exit 0
