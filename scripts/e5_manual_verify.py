"""Record E5's manual candidate build and offline run. No model calls or E6 changes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--run-dir', default='work/e5-01')
    parser.add_argument('--out', required=True, help='Fresh directory below work/, e.g. work/e5-01/manual-01')
    parser.add_argument('--build-timeout', type=int, default=600)
    parser.add_argument('--run-timeout', type=int, default=30)
    args = parser.parse_args()
    if sys.platform != 'linux':
        parser.error('Execute on the Linux experiment host with a working Docker daemon')
    if min(args.build_timeout, args.run_timeout) <= 0:
        parser.error('Timeouts must be positive')
    source = (ROOT / args.run_dir).resolve()
    candidate = (ROOT / args.candidate).resolve()
    out = (ROOT / args.out).resolve()
    if ROOT / 'work' not in out.parents or out.exists():
        parser.error('Use a fresh, nonexistent directory below this repository work/')
    baseline = source / 'iter-01'
    result = json.loads((baseline / 'result-retry.json').read_text(encoding='utf-8'))
    log = (baseline / 'build-retry.log').read_text(encoding='utf-8')
    if result.get('build_exit_code') in (None, 0, 124) or 'make: not found' not in log:
        parser.error('Baseline must contain actual missing-make build failure evidence')
    sys.path.insert(0, str(ROOT / 'services/draft'))
    from draft.autobuild import prepare_candidate, instructions
    text = candidate.read_text(encoding='utf-8')
    prepare_candidate((ROOT / 'fixtures/draft/Dockerfile.broken').read_text(encoding='utf-8'), text)
    if instructions(text)[0] != instructions((baseline / 'Dockerfile').read_text(encoding='utf-8'))[0]:
        parser.error('Candidate must preserve this run baseline exact FROM and digest')
    out.mkdir(parents=True)
    shutil.copy2(candidate, out / 'Dockerfile')
    summary = {'status': 'STARTED', 'time_utc': datetime.now(timezone.utc).isoformat(),
               'candidate_source': str(candidate), 'run_dir': str(source),
               'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
               'image_id': None, 'build_exit_code': None, 'verify_exit_code': None,
               'output_matches': None, 'commands': []}
    save(out / 'input-hashes.json', {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(source.rglob('*')) if p.is_file() and out not in p.parents})
    def execute(argv, stdout_name, stderr_name, timeout):
        record = {'argv': argv, 'cwd': str(ROOT), 'time_utc': datetime.now(timezone.utc).isoformat(),
                  'exit_code': None, 'timed_out': False}
        summary['commands'].append(record)
        save(out / 'result.json', summary)
        # Use separate streams unless deliberately recording a combined build log.
        with (out / stdout_name).open('wb') as stdout:
            stderr = stdout if stderr_name is None else (out / stderr_name).open('wb')
            try:
                record['exit_code'] = subprocess.run(argv, cwd=ROOT, stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                record['timed_out'] = True
            except OSError as exc:
                record['start_error'] = str(exc)
            finally:
                if stderr is not stdout:
                    stderr.close()
        save(out / 'result.json', summary)
        return record
    build = execute(['docker', 'build', '--progress=plain', '--iidfile', str(out / 'image-id.txt'),
                     '-f', str(out / 'Dockerfile'), str(source / 'project')],
                    'candidate-build.log', None, args.build_timeout)
    summary['build_exit_code'] = build['exit_code']
    if build['exit_code'] != 0 or build['timed_out']:
        summary['status'] = 'BUILD_FAILED_OR_INCOMPLETE'
        save(out / 'result.json', summary)
        return 1
    iid = (out / 'image-id.txt').read_text().strip()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', iid):
        summary['status'] = 'INVALID_IMAGE_ID'
        save(out / 'result.json', summary)
        return 1
    summary['image_id'] = iid
    inspect = execute(['docker', 'image', 'inspect', iid], 'image-inspect.json', 'image-inspect-stderr.log', 30)
    if inspect['exit_code'] != 0:
        summary['status'] = 'IMAGE_INSPECT_FAILED'
        save(out / 'result.json', summary)
        return 1
    if json.loads((out / 'image-inspect.json').read_text())[0]['Id'] != iid:
        summary['status'] = 'IMAGE_ID_MISMATCH'
        save(out / 'result.json', summary)
        return 1
    cidfile = out / 'runtime-container-id.txt'
    run = execute(['docker', 'run', '--rm', '--network', 'none', '--cidfile', str(cidfile), iid],
                  'verify.log', 'verify-stderr.log', args.run_timeout)
    summary['verify_exit_code'] = run['exit_code']
    if run['timed_out'] and cidfile.is_file():
        cid = cidfile.read_text().strip()
        if re.fullmatch(r'[0-9a-f]{64}', cid):
            execute(['docker', 'rm', '-f', cid], 'timeout-cleanup.log', 'timeout-cleanup-stderr.log', 30)
    summary['output_matches'] = (out / 'verify.log').read_bytes() in (b'hello E3', b'hello E3\n', b'hello E3\r\n')
    success = run['exit_code'] == 0 and not run['timed_out'] and summary['output_matches']
    summary['status'] = 'SUCCEEDED' if success else 'VERIFY_FAILED_OR_INCOMPLETE'
    save(out / 'result.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if success else 1

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f'ERROR: {exc}')
