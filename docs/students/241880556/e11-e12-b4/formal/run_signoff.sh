#!/usr/bin/env bash
set -euo pipefail

source_root=/root/241880556/devops-b09-e11-e12-b4
formal=/root/devops-submissions/241880556/e12-b4-formal-20261116-r2
signoff="$formal/signoff"
source_repo="$formal/data/integration-sample/repo"
report="$formal/work/e11-a-241880375/incremental-check.json"
repaired="$signoff/repaired-repo"
validation_project="$signoff/validation-project"
base=3fcb72029bf560afde2d29436395ff3b979a19fd
target=15c059958a41a5a0513dc048036439843a34ad28
report_sha=8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716
patch_sha=88074f66c291dcad1344c48f6a2b9ddd42d235d9d0415c85fb33310c5b7cb2af
candidate_image=sha256:f1fb7db7e04db01ee05e5ebfac0a02eab69953747e1649297e5ed63b691af076
environment_image=sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f

mkdir -p "$signoff"
test ! -e "$repaired"
printf '%s  %s\n' "$report_sha" "$report" | sha256sum --check > "$signoff/report-hash.log"
test "$(git -C "$source_repo" cat-file -t "$base")" = commit
test "$(git -C "$source_repo" cat-file -t "$target")" = commit
git -C "$source_repo" merge-base --is-ancestor "$base" "$target"
git clone --quiet "$source_repo" "$repaired"
git -C "$repaired" checkout --quiet -b b09-formal-repair "$target"
python3 "$source_root/labs/e11e12/repair_report.py" \
  --project "$repaired" --report "$report" --sha256 "$report_sha" \
  --kind incremental-check --out "$signoff/candidate.patch" \
  > "$signoff/receiver.log" 2>&1
test "$(sha256sum "$signoff/candidate.patch" | cut -d' ' -f1)" = "$patch_sha"
git -C "$repaired" apply --check "$signoff/candidate.patch"
git -C "$repaired" apply "$signoff/candidate.patch"
git -C "$repaired" add Makefile
git -C "$repaired" -c user.name='B09 241880556' \
  -c user.email='241880556@students.example.invalid' \
  commit --quiet -m 'fix: declare main.o header dependencies'
git -C "$repaired" rev-parse HEAD > "$signoff/repaired-commit.txt"
test "$(git -C "$repaired" rev-parse HEAD^)" = "$target"
git -C "$repaired" status --porcelain > "$signoff/repaired-status.log"
test ! -s "$signoff/repaired-status.log"

docker run --rm --network none -v "$repaired:/work" -w /work \
  "$candidate_image" sh -lc 'make clean && make app && ./app' \
  > "$signoff/build.log" 2>&1
test "$(tail -1 "$signoff/build.log")" = 1
cp -a "$repaired" "$validation_project"
sed -i 's/#define VALUE 1/#define VALUE 2/' "$validation_project/config.h"
docker run --rm --network none -v "$validation_project:/work" -w /work \
  "$candidate_image" sh -lc 'make app && ./app' \
  > "$signoff/incremental.log" 2>&1
grep -q 'gcc .* -c main.c -o main.o' "$signoff/incremental.log"
test "$(tail -1 "$signoff/incremental.log")" = 2

mkdir -p "$signoff/recheck"
chmod 777 "$signoff/recheck"
docker run --rm --network none --cap-add SYS_PTRACE \
  -v "$repaired:/fixture:ro" -v "$signoff/recheck:/out" \
  "$environment_image" python3 -m buildchecker full-check \
  --fixture /fixture --out /out \
  > "$signoff/recheck.json" 2> "$signoff/recheck-stderr.log"

python3 - "$signoff" <<'PY'
import hashlib, json, sys
from pathlib import Path
out = Path(sys.argv[1])
report = json.loads((out.parent / 'work/e11-a-241880375/incremental-check.json').read_text())
recheck = json.loads((out / 'recheck.json').read_text())
assert report['job_id'] == 'job-1bd0ed1b449f44f293853df90440844f'
assert report['trace_id'] == 'trace-4e7c0c6afd0447f9869d2f5e1ee6f4ae'
assert recheck['status'] == 'SUCCEEDED'
missing = [finding for finding in recheck['findings'] if finding['type'] == 'MISSING']
assert not missing, missing
digest = lambda name: hashlib.sha256((out / name).read_bytes()).hexdigest()
validation = {
    'schema_version': 'e12-b4-a09-signoff-1',
    'accepted': True,
    'job_id': report['job_id'],
    'trace_id': report['trace_id'],
    'a_job_id': report['job_id'],
    'a_trace_id': report['trace_id'],
    'base_commit': '3fcb72029bf560afde2d29436395ff3b979a19fd',
    'target_commit': report['commit'],
    'repaired_commit': (out / 'repaired-commit.txt').read_text().strip(),
    'source_report_kind': report['kind'],
    'source_report_sha256': '8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716',
    'candidate_patch_sha256': digest('candidate.patch'),
    'build_log_sha256': digest('build.log'),
    'incremental_log_sha256': digest('incremental.log'),
    'recheck_report_sha256': digest('recheck.json'),
    'candidate_image_id': 'sha256:f1fb7db7e04db01ee05e5ebfac0a02eab69953747e1649297e5ed63b691af076',
    'environment_image_id': 'sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f',
    'build_command': 'make clean && make app',
    'run_command': './app',
    'program_output': '1',
    'incremental_main_rebuilt': True,
    'program_after_config_change': '2',
    'recheck_missing_count': 0,
    'recheck_remaining_findings': recheck['findings'],
}
(out / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation, indent=2))
PY
