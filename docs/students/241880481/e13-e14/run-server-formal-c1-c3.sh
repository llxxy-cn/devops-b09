#!/usr/bin/env bash
# B09 / 241880481 / E13 formal C1-C3 server runner.
# Run from the B09 repository root. MATERIAL_DIR must be below that root and
# contain the two exchange directories copied from A09 fixed head 269827d...

set -uo pipefail

usage() {
  cat <<'EOF'
Usage: bash docs/students/241880481/e13-e14/run-server-formal-c1-c3.sh MATERIAL_DIR

Runs formal E13 C1 (success), C2 (STALE_REPORT), C3
(ARTIFACT_HASH_MISMATCH), and a clean recovery run. MATERIAL_DIR must contain:
  exchange-a09-to-b09/
  exchange-b09-to-a09/

Every formal pipeline command, exit code, request, assertion, and output is
retained below a new work/e13-b1-server-formal-* directory. No push or external
message occurs.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then usage; exit 0; fi
if [[ $# -ne 1 ]]; then usage >&2; exit 2; fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: run inside the B09 repository" >&2; exit 2;
}
cd "$REPO_ROOT"
MATERIAL_DIR="$(realpath "$1")"
case "$MATERIAL_DIR/" in "$REPO_ROOT"/*) ;; *)
  echo "ERROR: MATERIAL_DIR must be below $REPO_ROOT" >&2; exit 2;; esac

A09="$MATERIAL_DIR/exchange-a09-to-b09"
B09="$MATERIAL_DIR/exchange-b09-to-a09"
[[ -d "$A09" && -d "$B09" ]] || {
  echo "ERROR: missing exchange-a09-to-b09 or exchange-b09-to-a09" >&2; exit 2;
}

BASE=e825395a5f8006f1c57a115cc25ea5c7802863ee
TARGET=ba688c40d13cd8658e554f7544f1546d35b4b397
A_JOB=job-131c4b1d8c34469aaa31f9e2a9da1736
A_TRACE=trace-c224eaab92394b91bedfc2dea14ebc61
A_REPORT_SHA=504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224
A_REPORT_BYTES=3052
RUN_ID="$(date +%Y%m%d-%H%M%S)"
EVIDENCE_ROOT="$REPO_ROOT/work/e13-b1-server-formal-$RUN_ID"
mkdir -p "$EVIDENCE_ROOT"/{inputs,c1,c2,c3,recovery,deliverables,raw-a09}
SUMMARY="$EVIDENCE_ROOT/summary.tsv"
ASSERTIONS="$EVIDENCE_ROOT/assertions.log"
printf 'step\texit_code\tlog\n' > "$SUMMARY"
: > "$ASSERTIONS"
FAILURES=0

run_step() {
  local step="$1"; shift
  local log="$EVIDENCE_ROOT/${step//\//-}.log"
  {
    printf 'START_UTC=%s\nPWD=%s\nCOMMAND=' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$PWD"
    printf '%q ' "$@"; printf '\n'
  } > "$log"
  set +e
  "$@" >> "$log" 2>&1
  local rc=$?
  set -e
  printf 'EXIT_CODE=%s\nEND_UTC=%s\n' "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$log"
  printf '%s\t%s\t%s\n' "$step" "$rc" "$log" >> "$SUMMARY"
  printf '%s\n' "$rc" > "$EVIDENCE_ROOT/${step//\//-}.exitcode"
  return 0
}

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    printf 'ASSERT_OK %s=%s\n' "$label" "$actual" | tee -a "$ASSERTIONS"
  else
    printf 'ASSERT_FAIL %s expected=%s actual=%s\n' "$label" "$expected" "$actual" | tee -a "$ASSERTIONS"
    FAILURES=$((FAILURES + 1))
  fi
}

step_rc() { tr -d '\r\n' < "$EVIDENCE_ROOT/${1//\//-}.exitcode"; }
sha() { sha256sum "$1" | awk '{print $1}'; }

echo "SERVER_EVIDENCE_DIR=$EVIDENCE_ROOT"
set -e

run_step git-identity bash -lc 'git config --local user.name 241880481 && git config --local user.email 241880481@example.invalid'
assert_eq git_identity_rc 0 "$(step_rc git-identity)"
run_step context bash -lc 'uname -a; id; python3 --version; git --version; docker version; git status --short --branch; git rev-parse HEAD; docker image inspect course-e11e12:241880481 --format "{{.Id}}"'
assert_eq context_rc 0 "$(step_rc context)"

# Verify both directions before interpreting either report.
declare -A EXPECTED=(
  ["$A09/a09-e13-project.bundle"]=40510b4c02a05b0ce372ee7870c53ca4d4f32978599e93d8c7ac1b3a2e319072
  ["$A09/candidate.Dockerfile"]=6f0e3980c609a683d727c271bdd3a8d5f12b46df21f1fcc402e0d8420ce06c28
  ["$A09/result.json"]=3fd3be33d41b95e9fff9762fac1b2413c649f68714f06c4b4520f3e52e769015
  ["$A09/full-check.json"]=c9de4bb36f114f9caad7111d918dde2475a080667f401f8ec707f7772686d549
  ["$A09/incremental-check.json"]=$A_REPORT_SHA
  ["$A09/a09-e13-detection-evidence.tar.gz"]=ee7a35a373e5e5e5a7b3d95d7533d671d9d75858494e2aeafc51f70c2e73c128
  ["$B09/result.json"]=4e528cb510c736876e6aacaf4bf0244fe4ea56fe5cda33e63eac46e6232a3602
  ["$B09/full-check.json"]=af401bfd6795266cc474d364dddc49c9df7b8831d39665bf9828e30f2b9a8f55
  ["$B09/incremental-check.json"]=6fd68688873fdd1aa24ea5de5c5d9202580e560bc62ff476f7363d0f442a7f04
  ["$B09/e13-c1-b09-detection-evidence.tar.gz"]=22241fb4430cbeb7431f1b31e6b3e1bc4afd8c6eaf90c1f56f18fa94e9830784
)
for file in "${!EXPECTED[@]}"; do
  [[ -f "$file" ]] || { echo "missing $file" >&2; exit 3; }
  assert_eq "sha256:$(basename "$file")" "${EXPECTED[$file]}" "$(sha "$file")"
done
assert_eq incremental_bytes "$A_REPORT_BYTES" "$(stat -c %s "$A09/incremental-check.json")"
[[ $FAILURES -eq 0 ]] || { echo "FAILURES=$FAILURES"; exit 1; }

# Reject dangerous archive entries before extraction.
run_step safe-extract python3 - "$A09/a09-e13-detection-evidence.tar.gz" "$EVIDENCE_ROOT/raw-a09" <<'PY'
import pathlib, sys, tarfile
archive, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
with tarfile.open(archive, "r:gz") as tf:
    for item in tf.getmembers():
        p = pathlib.PurePosixPath(item.name)
        if p.is_absolute() or ".." in p.parts or item.issym() or item.islnk() or item.isdev():
            raise SystemExit(f"unsafe archive member: {item.name}")
    tf.extractall(out)
PY
assert_eq safe_extract_rc 0 "$(step_rc safe-extract)"
RAW_RESULT="$(find "$EVIDENCE_ROOT/raw-a09" -type f -name result.json -print -quit)"
[[ -n "$RAW_RESULT" ]] || { echo "ERROR: raw A09 result absent" >&2; exit 3; }

run_step clone-project git clone -q "$A09/a09-e13-project.bundle" "$EVIDENCE_ROOT/input-project"
assert_eq clone_rc 0 "$(step_rc clone-project)"
run_step project-identity bash -lc "git -C '$EVIDENCE_ROOT/input-project' cat-file -e '$BASE^{commit}' && git -C '$EVIDENCE_ROOT/input-project' cat-file -e '$TARGET^{commit}' && git -C '$EVIDENCE_ROOT/input-project' merge-base --is-ancestor '$BASE' '$TARGET' && git -C '$EVIDENCE_ROOT/input-project' checkout -q --detach '$TARGET'"
assert_eq project_identity_rc 0 "$(step_rc project-identity)"
ORIGINAL_MAKEFILE_SHA="$(sha "$EVIDENCE_ROOT/input-project/Makefile")"

HANDOFF="$EVIDENCE_ROOT/inputs/fixed-md-a09.json"
run_step make-handoff python3 labs/e13e14/handoff_a_to_b.py --a-result "$RAW_RESULT" --target-sha "$TARGET" --out "$HANDOFF"
assert_eq handoff_rc 0 "$(step_rc make-handoff)"
HANDOFF_SHA="$(sha "$HANDOFF")"

run_step source-identity python3 - "$HANDOFF" <<PY
import json, sys
x=json.load(open(sys.argv[1], encoding='utf-8')); s=x['source_report']
assert x['commit']=='$TARGET' and x['data']['commit']=='$TARGET'
assert s=={'job_id':'$A_JOB','trace_id':'$A_TRACE','uri':'artifact://$A_JOB/incremental-check.json','sha256':'$A_REPORT_SHA','bytes':$A_REPORT_BYTES}
PY
assert_eq source_identity_rc 0 "$(step_rc source-identity)"
[[ $FAILURES -eq 0 ]] || { echo "FAILURES=$FAILURES"; exit 1; }

write_request() {
  local out="$1" target="$2" report="$3" declared_sha="$4"
  python3 - "$out" "$target" "$report" "$declared_sha" "$REPO_ROOT" "$EVIDENCE_ROOT" "$A09" <<'PY'
import json, pathlib, sys
root=pathlib.Path(sys.argv[5]); ev=pathlib.Path(sys.argv[6]); exchange=pathlib.Path(sys.argv[7])
inside=lambda p: '/course/'+pathlib.Path(p).resolve().relative_to(root).as_posix()
x={'mode':'e11-b','repo':inside(ev/'input-project'),'base':'e825395a5f8006f1c57a115cc25ea5c7802863ee','target':sys.argv[2],
   'candidate':inside(exchange/'candidate.Dockerfile'),'expected_output':'1','build_timeout':600,
   'fixed_report':inside(sys.argv[3]),'fixed_report_sha256':sys.argv[4],
   'project_compat':{'layout':'root-make','make_test':False},
   'expected_source_report':{'job_id':'job-131c4b1d8c34469aaa31f9e2a9da1736','trace_id':'trace-c224eaab92394b91bedfc2dea14ebc61','uri':'artifact://job-131c4b1d8c34469aaa31f9e2a9da1736/incremental-check.json','sha256':'504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224','bytes':3052}}
pathlib.Path(sys.argv[1]).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
PY
}

write_request "$EVIDENCE_ROOT/inputs/request-c1.json" "$TARGET" "$HANDOFF" "$HANDOFF_SHA"
write_request "$EVIDENCE_ROOT/inputs/request-c2.json" "$BASE" "$HANDOFF" "$HANDOFF_SHA"
cp "$HANDOFF" "$EVIDENCE_ROOT/inputs/fixed-md-a09-tampered.json"
printf '\n' >> "$EVIDENCE_ROOT/inputs/fixed-md-a09-tampered.json"
TAMPER_SHA="$(sha "$EVIDENCE_ROOT/inputs/fixed-md-a09-tampered.json")"
write_request "$EVIDENCE_ROOT/inputs/request-c3.json" "$TARGET" "$EVIDENCE_ROOT/inputs/fixed-md-a09-tampered.json" "$HANDOFF_SHA"

rel() { realpath --relative-to="$REPO_ROOT" "$1"; }
run_case() {
  local name="$1"
  run_step "$name/pipeline" python3 run_e11e12.py run --request "$(rel "$EVIDENCE_ROOT/inputs/request-$name.json")" --out "$(rel "$EVIDENCE_ROOT/$name/run")"
}

run_case c1
assert_eq c1_exit 0 "$(step_rc c1/pipeline)"
run_step c1/assert python3 - "$EVIDENCE_ROOT/c1/run" "$EVIDENCE_ROOT/input-project" "$TARGET" "$ORIGINAL_MAKEFILE_SHA" <<'PY'
import hashlib,json,pathlib,subprocess,sys
r=pathlib.Path(sys.argv[1]); result=json.load(open(r/'result.json',encoding='utf-8'))
assert result['status']=='SUCCEEDED'
assert [x['name'] for x in result['stages']]==['draft','fixed-md','repair','recheck']
plan=json.load(open(r/'repair-plan.json',encoding='utf-8'))
want={('main.o','calculate.h'),('main.o','config.h'),('main.o','extra.h'),('helper.o','add.h'),('helper.o','calculate.h'),('helper.o','sub.h')}
assert {(x['target'],x['dependency']) for x in plan}==want
edges=json.load(open(r/'validation/edge-rebuilds.json',encoding='utf-8'))
assert len(edges)==6 and all(x['rebuilt'] and x['output_matches'] for x in edges)
for path in (r/'validation/recheck.json',r/'final-full/findings.json'):
    findings=json.load(open(path,encoding='utf-8'))['findings']
    assert not [x for x in findings if x['type']=='MISSING']
    assert [(x['target'],x['dependency']) for x in findings if x['type']=='REDUNDANT']==[('main.o','unused.h')]
prefix=f"artifact://{result['job_id']}/"
for x in result['artifacts']:
    assert x['uri'].startswith(prefix); p=r/x['uri'][len(prefix):]
    assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'] and p.stat().st_size==x['bytes']
repo=pathlib.Path(sys.argv[2])
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==sys.argv[3]
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
assert hashlib.sha256((repo/'Makefile').read_bytes()).hexdigest()==sys.argv[4]
print('B_JOB_ID='+result['job_id']); print('B_TRACE_ID='+result['trace_id']); print('ARTIFACTS_VERIFIED='+str(len(result['artifacts'])))
PY
assert_eq c1_assert_rc 0 "$(step_rc c1/assert)"

run_case c2
assert_eq c2_exit 1 "$(step_rc c2/pipeline)"
run_step c2/assert python3 - "$EVIDENCE_ROOT/c2/run" "$EVIDENCE_ROOT/input-project" "$TARGET" "$ORIGINAL_MAKEFILE_SHA" <<'PY'
import json,pathlib,sys
r=pathlib.Path(sys.argv[1]); repo=pathlib.Path(sys.argv[2]); x=json.load(open(r/'result.json',encoding='utf-8'))
assert x['status']=='FAILED' and x['error']['code']=='STALE_REPORT'
assert not (r/'draft-build').exists() and not (r/'candidate.patch').exists() and not (r/'validation'/'sandbox').exists()
import hashlib,subprocess
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==sys.argv[3]
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
assert hashlib.sha256((repo/'Makefile').read_bytes()).hexdigest()==sys.argv[4]
PY
assert_eq c2_assert_rc 0 "$(step_rc c2/assert)"

run_case c3
assert_eq c3_exit 1 "$(step_rc c3/pipeline)"
run_step c3/assert python3 - "$EVIDENCE_ROOT/c3/run" "$HANDOFF_SHA" "$TAMPER_SHA" "$EVIDENCE_ROOT/input-project" "$TARGET" "$ORIGINAL_MAKEFILE_SHA" <<'PY'
import json,pathlib,sys
r=pathlib.Path(sys.argv[1]); x=json.load(open(r/'result.json',encoding='utf-8'))
assert sys.argv[2]!=sys.argv[3]
assert x['status']=='FAILED' and x['error']['code']=='ARTIFACT_HASH_MISMATCH'
assert not (r/'draft-build').exists() and not (r/'candidate.patch').exists() and not (r/'validation'/'sandbox').exists()
import hashlib,subprocess
repo=pathlib.Path(sys.argv[4])
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==sys.argv[5]
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
assert hashlib.sha256((repo/'Makefile').read_bytes()).hexdigest()==sys.argv[6]
PY
assert_eq c3_assert_rc 0 "$(step_rc c3/assert)"

cp "$EVIDENCE_ROOT/inputs/request-c1.json" "$EVIDENCE_ROOT/inputs/request-recovery.json"
run_step recovery/pipeline python3 run_e11e12.py run --request "$(rel "$EVIDENCE_ROOT/inputs/request-recovery.json")" --out "$(rel "$EVIDENCE_ROOT/recovery/run")"
assert_eq recovery_exit 0 "$(step_rc recovery/pipeline)"
run_step recovery/assert python3 - "$EVIDENCE_ROOT/recovery/run/result.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1],encoding='utf-8')); assert x['status']=='SUCCEEDED'
print('RECOVERY_JOB_ID='+x['job_id']); print('RECOVERY_TRACE_ID='+x['trace_id'])
PY
assert_eq recovery_assert_rc 0 "$(step_rc recovery/assert)"

# Create the fixed commit only in an independent clone; its parent is TARGET.
run_step fixed/clone git clone -q "$A09/a09-e13-project.bundle" "$EVIDENCE_ROOT/fixed-project"
assert_eq fixed_clone_rc 0 "$(step_rc fixed/clone)"
run_step fixed/apply bash -lc "git -C '$EVIDENCE_ROOT/fixed-project' checkout -q -B b09-e13-fixed '$TARGET' && git -C '$EVIDENCE_ROOT/fixed-project' apply '$EVIDENCE_ROOT/c1/run/candidate.patch' && git -C '$EVIDENCE_ROOT/fixed-project' -c user.name=241880481 -c user.email=241880481@example.invalid commit -qam 'fix: declare observed Make dependencies'"
assert_eq fixed_apply_rc 0 "$(step_rc fixed/apply)"
FIXED_COMMIT="$(git -C "$EVIDENCE_ROOT/fixed-project" rev-parse HEAD)"
assert_eq fixed_parent "$TARGET" "$(git -C "$EVIDENCE_ROOT/fixed-project" rev-parse HEAD^)"
git -C "$EVIDENCE_ROOT/fixed-project" diff "$TARGET" "$FIXED_COMMIT" > "$EVIDENCE_ROOT/deliverables/fixed.diff"
git -C "$EVIDENCE_ROOT/fixed-project" bundle create "$EVIDENCE_ROOT/deliverables/a09-e13-project-fixed.bundle" b09-e13-fixed
cp "$EVIDENCE_ROOT/c1/run/candidate.patch" "$EVIDENCE_ROOT/deliverables/"
cp "$EVIDENCE_ROOT/c1/run/validation/validation.json" "$EVIDENCE_ROOT/deliverables/"
cp "$EVIDENCE_ROOT/c1/run/validation/edge-rebuilds.json" "$EVIDENCE_ROOT/deliverables/"
cp "$EVIDENCE_ROOT/c1/run/final-full/findings.json" "$EVIDENCE_ROOT/deliverables/final-recheck.json"

run_step deliverables/manifest bash -lc "cd '$EVIDENCE_ROOT/deliverables' && sha256sum * > SHA256SUMS && printf 'FIXED_COMMIT=%s\nFIXED_PARENT=%s\nSOURCE_JOB=%s\nSOURCE_TRACE=%s\n' '$FIXED_COMMIT' '$TARGET' '$A_JOB' '$A_TRACE' > identities.txt"
assert_eq manifest_rc 0 "$(step_rc deliverables/manifest)"

printf 'ORIGINAL_HANDOFF_SHA256=%s\nTAMPERED_HANDOFF_SHA256=%s\nFIXED_COMMIT=%s\n' "$HANDOFF_SHA" "$TAMPER_SHA" "$FIXED_COMMIT" | tee "$EVIDENCE_ROOT/identities.txt"
printf 'FAILURES=%s\nSERVER_EVIDENCE_DIR=%s\n' "$FAILURES" "$EVIDENCE_ROOT" | tee -a "$ASSERTIONS"
echo "SERVER_EVIDENCE_DIR=$EVIDENCE_ROOT"
echo "FAILURES=$FAILURES"
[[ $FAILURES -eq 0 ]]
