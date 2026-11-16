#!/usr/bin/env bash
set -euo pipefail

repo=/root/241880556/devops-b09-e11-e12-b4
out=/root/devops-submissions/241880556/e12-b4-formal-20261116-r2
archive="$out/a-original.tar.gz"
report="$out/work/e11-a-241880375/incremental-check.json"
full_report="$out/work/e11-a-241880375/full-check.json"
project="$out/target-project"
patch="$out/candidate.patch"
base=3fcb72029bf560afde2d29436395ff3b979a19fd
target=15c059958a41a5a0513dc048036439843a34ad28
archive_sha=19479d51720decbca2518453e00646a4700c7b21101b018965bfdbc0c8cce648
report_sha=8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716
full_report_sha=59c602db2c12075f66fc754fdfdb78d832dc5f83f99391b1c3ddcf29cdd6beef
candidate_image=sha256:f1fb7db7e04db01ee05e5ebfac0a02eab69953747e1649297e5ed63b691af076
environment_image=sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f

mkdir -p "$out"
if [[ ! -s "$archive" ]]; then
  curl --fail --location --silent --show-error --connect-timeout 15 --max-time 90 \
    'https://raw.githubusercontent.com/a-bi-chen/DevOps_1020_Student_Cloud/0cd8054911a18be96900e05c3b7747c6b35a4112/evidence/students/241880375/e11-e12/e11e12-evidence-241880375.tar.gz' \
    --output "$archive"
fi
printf '%s  %s\n' "$archive_sha" "$archive" | sha256sum --check | tee "$out/archive-verify.log"
tar -xzf "$archive" -C "$out" \
  data/integration-sample/repo \
  data/integration-sample/dataset.json \
  work/e11-a-241880375/incremental-check.json \
  work/e11-a-241880375/full-check.json
printf '%s  %s\n' "$report_sha" "$report" | sha256sum --check | tee "$out/report-verify.log"
printf '%s  %s\n' "$full_report_sha" "$full_report" | sha256sum --check | tee "$out/full-report-verify.log"

source_project="$out/data/integration-sample/repo"
test "$(git -C "$source_project" cat-file -t "$base")" = commit
test "$(git -C "$source_project" cat-file -t "$target")" = commit
git -C "$source_project" merge-base --is-ancestor "$base" "$target"
git -C "$source_project" log --format='%H %s' --all > "$out/project-commits.log"
git clone --quiet "$source_project" "$project"
git -C "$project" checkout --quiet "$target"
test "$(git -C "$project" rev-parse HEAD)" = "$target"
git -C "$project" status --porcelain > "$out/target-before-status.log"
test ! -s "$out/target-before-status.log"

python3 "$repo/labs/e11e12/repair_report.py" \
  --project "$project" --report "$report" --sha256 "$report_sha" \
  --kind incremental-check --out "$patch" | tee "$out/receiver.log"
sha256sum "$patch" | tee "$out/patch.sha256"
git -C "$project" apply --check "$patch" 2>&1 | tee "$out/apply-check.log"
git -C "$project" apply "$patch"
git -C "$project" diff -- Makefile > "$out/applied.diff"

docker image inspect "$candidate_image" --format '{{.Id}}' > "$out/candidate-image-id.txt"
docker image inspect "$environment_image" --format '{{.Id}}' > "$out/environment-image-id.txt"
docker run --rm --network none -v "$project:/work" -w /work \
  "$candidate_image" sh -lc 'make clean && make app && ./app' \
  > "$out/build-and-program.log" 2>&1
test "$(tail -1 "$out/build-and-program.log")" = 1
sed -i 's/#define VALUE 1/#define VALUE 2/' "$project/config.h"
docker run --rm --network none -v "$project:/work" -w /work \
  "$candidate_image" sh -lc 'make app && ./app' \
  > "$out/header-rebuild-and-program.log" 2>&1
grep -q 'gcc .* -c main.c -o main.o' "$out/header-rebuild-and-program.log"
test "$(tail -1 "$out/header-rebuild-and-program.log")" = 2

mkdir -p "$out/recheck"
chmod 777 "$out/recheck"
docker run --rm --network none --cap-add SYS_PTRACE \
  -v "$project:/fixture:ro" -v "$out/recheck:/out" \
  "$environment_image" python3 -m buildchecker full-check \
  --fixture /fixture --out /out \
  > "$out/recheck-console.json" 2> "$out/recheck-stderr.log"

python3 - "$report" "$out/recheck-console.json" "$out/summary.json" <<'PY'
import json, sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text())
recheck = json.loads(Path(sys.argv[2]).read_text())
assert report['schema_version'] == 'e11e12-1'
assert report['kind'] == 'incremental-check'
assert report['status'] == 'SUCCEEDED'
assert report['job_id'] == 'job-1bd0ed1b449f44f293853df90440844f'
assert report['trace_id'] == 'trace-4e7c0c6afd0447f9869d2f5e1ee6f4ae'
assert recheck['status'] == 'SUCCEEDED'
missing = [f for f in recheck['findings'] if f['type'] == 'MISSING']
assert not missing, missing
summary = {
    'status': 'SUCCEEDED',
    'a_job_id': report['job_id'],
    'a_trace_id': report['trace_id'],
    'base_commit': '3fcb72029bf560afde2d29436395ff3b979a19fd',
    'target_commit': report['commit'],
    'a_archive_sha256': '19479d51720decbca2518453e00646a4700c7b21101b018965bfdbc0c8cce648',
    'a_report_sha256': '8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716',
    'candidate_patch_sha256': __import__('hashlib').sha256(Path(sys.argv[3]).with_name('candidate.patch').read_bytes()).hexdigest(),
    'candidate_image_id': Path(sys.argv[3]).with_name('candidate-image-id.txt').read_text().strip(),
    'environment_image_id': Path(sys.argv[3]).with_name('environment-image-id.txt').read_text().strip(),
    'program_before': '1', 'program_after_header_change': '2',
    'recheck_missing_count': 0,
    'recheck_remaining_findings': recheck['findings'],
}
Path(sys.argv[3]).write_text(json.dumps(summary, indent=2) + '\n')
PY
cat "$out/summary.json"
