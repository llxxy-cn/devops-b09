"""Run E14's four Compose services on one pinned teaching project."""
import argparse
import errno
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

PORTS = {
    'buildchecker': int(os.environ.get('E14_BUILDCHECKER_PORT', '18081')),
    'echecker': int(os.environ.get('E14_ECHECKER_PORT', '18082')),
    'draft': int(os.environ.get('E14_DRAFT_PORT', '18083')),
    'mdfixer': int(os.environ.get('E14_MDFIXER_PORT', '18084')),
}
ROOT = Path(__file__).resolve().parents[2]
MAX_CONNECT_ATTEMPTS = 3
RETRY_DELAYS = (0.25, 0.5)


class ServiceCallError(Exception):
    def __init__(self, role, error_code, attempts, message):
        super().__init__(f'{role}: {message}')
        self.role = role
        self.error_code = error_code
        self.attempts = attempts


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def container_path(path):
    return '/course/' + path.resolve().relative_to(ROOT.resolve()).as_posix()


def host_path(value):
    if not isinstance(value, str) or not value.startswith('/course/'):
        raise ValueError('Expected /course path')
    path = (ROOT / value[len('/course/'):]).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError('Path escapes repository')
    return path


def command(argv, cwd, log):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(p.stdout + p.stderr, encoding='utf-8')
    if p.returncode:
        raise ValueError(f'{argv[0]} failed; inspect {log}')
    return p.stdout.strip()


def snapshot(repo, revision, target, logs, project_subdir=None):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Use a full Git commit SHA')
    head = command(['git', 'rev-parse', '--verify', revision + '^{commit}'], repo,
                   logs / (target.name + '-resolve.log'))
    command(['git', 'clone', '--no-hardlinks', '--no-checkout', str(repo), str(target)], repo,
            logs / (target.name + '-clone.log'))
    if project_subdir is not None:
        if (not isinstance(project_subdir, str) or not project_subdir
            or '\\' in project_subdir or any(part in ('', '.', '..', '.git') for part in project_subdir.split('/'))):
            raise ValueError('Invalid project_subdir')
        command(['git', 'sparse-checkout', 'set', '--cone', '--', project_subdir], target,
                logs / (target.name + '-sparse.log'))
    command(['git', 'checkout', '--detach', head], target, logs / (target.name + '-checkout.log'))
    project = target
    if project_subdir is not None:
        project = (target / project_subdir).resolve()
        if not project.is_relative_to(target.resolve()):
            raise ValueError('project_subdir escapes repository')
    if {p.name for p in project.glob('*.c')} != {'main.c', 'helper.c'} or not (project / 'config.h').is_file():
        raise ValueError('Unsupported teaching project profile')
    return head, project


def offline_baseline(project, candidate, config):
    """Temporarily align DRAFT's broken baseline with a verified local base image."""
    original_candidate = host_path(config['original_candidate'])
    if digest(original_candidate) != config['original_candidate_sha256']:
        raise ValueError('Original candidate hash mismatch')
    if digest(candidate) != config['derived_candidate_sha256']:
        raise ValueError('Derived candidate hash mismatch')
    base_image = config['base_image']
    base_id = config['base_image_id']
    if not re.fullmatch(r'[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+', base_image):
        raise ValueError('Invalid offline base image tag')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', base_id):
        raise ValueError('Invalid offline base image ID')
    actual_id = command(['docker', 'image', 'inspect', base_image, '--format', '{{.Id}}'],
                        ROOT, project.parent / 'offline-image-inspect.log')
    if actual_id != base_id:
        raise ValueError('Offline base image ID mismatch')
    original_from = original_candidate.read_text(encoding='utf-8').splitlines()[0]
    derived_from = candidate.read_text(encoding='utf-8').splitlines()[0]
    if derived_from != f'FROM {base_image}@{base_id}':
        raise ValueError('Derived candidate does not use verified offline image')
    broken = project / 'Dockerfile.broken'
    before = broken.read_bytes()
    lines = before.decode('utf-8').splitlines(keepends=True)
    if not lines or lines[0].strip() != original_from.split('@', 1)[0]:
        raise ValueError('Broken Dockerfile does not match original candidate base')
    lines[0] = f'FROM {base_image}\n'
    broken.write_text(''.join(lines), encoding='utf-8')
    mapping = {'original_candidate': config['original_candidate'],
               'original_candidate_sha256': digest(original_candidate),
               'derived_candidate_sha256': digest(candidate),
               'base_image': base_image, 'base_image_id': base_id,
               'original_broken_sha256': hashlib.sha256(before).hexdigest(),
               'temporary_broken_sha256': digest(broken)}
    return broken, before, mapping


def call(role, payload, evidence):
    req = urllib.request.Request(f'http://127.0.0.1:{PORTS[role]}/v1/run',
                                 data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    attempts = []
    attempt_log = evidence.with_name(evidence.stem + '-attempts.json')
    for number in range(1, MAX_CONNECT_ATTEMPTS + 1):
        started_at_utc = datetime.now(timezone.utc).isoformat()
        try:
            with urllib.request.urlopen(req, timeout=720) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors='replace')
            try:
                response = json.loads(body)
            except json.JSONDecodeError:
                response = {}
            code = response.get('error_code') if isinstance(response, dict) else None
            code = code or f'HTTP_{exc.code}'
            attempts.append({'attempt': number, 'started_at_utc': started_at_utc,
                             'http': exc.code, 'error_code': code})
            retry = exc.code == 503 and code == 'SERVICE_BUSY' and number < MAX_CONNECT_ATTEMPTS
            if retry:
                time.sleep(RETRY_DELAYS[number - 1])
                continue
            save(evidence, {'role': role, 'http': exc.code, 'error_code': code, 'error': body})
            save(attempt_log, attempts)
            raise ServiceCallError(role, code, number, f'HTTP {exc.code}: {body}') from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            refused = isinstance(reason, ConnectionRefusedError) or (
                isinstance(reason, OSError) and reason.errno == errno.ECONNREFUSED)
            code = 'DOWNSTREAM_UNAVAILABLE' if refused else 'DOWNSTREAM_TRANSPORT_ERROR'
            attempts.append({'attempt': number, 'started_at_utc': started_at_utc,
                             'error_code': code, 'error': str(exc)})
            if refused and number < MAX_CONNECT_ATTEMPTS:
                time.sleep(RETRY_DELAYS[number - 1])
                continue
            save(evidence, {'role': role, 'error_code': code, 'error': str(exc)})
            save(attempt_log, attempts)
            raise ServiceCallError(role, code, number, str(exc)) from exc
        except TimeoutError as exc:
            code = 'DOWNSTREAM_TIMEOUT'
            attempts.append({'attempt': number, 'started_at_utc': started_at_utc,
                             'error_code': code, 'error': str(exc)})
            save(evidence, {'role': role, 'error_code': code, 'error': str(exc)})
            save(attempt_log, attempts)
            raise ServiceCallError(role, code, number, str(exc)) from exc
        if not isinstance(data, dict):
            code = 'INVALID_SERVICE_RESPONSE'
            attempts.append({'attempt': number, 'started_at_utc': started_at_utc,
                             'http': 200, 'error_code': code})
            save(evidence, {'role': role, 'error_code': code, 'error': 'Expected a JSON object'})
            save(attempt_log, attempts)
            raise ServiceCallError(role, code, number, 'Expected a JSON object')
        attempts.append({'attempt': number, 'started_at_utc': started_at_utc,
                         'http': 200, 'status': data.get('status')})
        save(evidence, data)
        save(attempt_log, attempts)
        if data.get('status') != 'SUCCEEDED':
            code = data.get('error_code') or 'DOWNSTREAM_FAILED'
            raise ServiceCallError(role, code, number, 'service did not succeed')
        return data


def execute(request, out):
    if out.exists():
        raise ValueError('Use a new output directory')
    if not out.resolve().is_relative_to((ROOT / 'work').resolve()):
        raise ValueError('Output must be inside work/')
    repo = host_path(request['repo'])
    candidate = host_path(request['candidate'])
    if not repo.resolve().is_relative_to((ROOT / 'data').resolve()) or not candidate.resolve().is_relative_to((ROOT / 'data').resolve()):
        raise ValueError('Input project and candidate must be in data/')
    out.mkdir(parents=True)
    job = 'job-' + uuid.uuid4().hex
    trace = 'trace-' + uuid.uuid4().hex
    result = {'schema_version': 'e14-compose-1', 'job_id': job, 'trace_id': trace,
              'status': 'RUNNING', 'stages': []}
    save(out / 'request.json', request)

    def payload(project, folder, **extra):
        return {'project': container_path(project), 'out': container_path(folder),
                'job_id': job, 'trace_id': trace, **extra}

    def stage(name, commit, data):
        item = {'name': name, 'commit': commit, 'job_id': job, 'trace_id': trace, 'status': 'SUCCEEDED', 'data': data}
        path = out / (name + '.json')
        save(path, item)
        result['stages'].append({'name': name, 'artifact': {'uri': path.name, 'sha256': digest(path)}})

    try:
        base = out / 'base-project'
        target = out / 'target-project'
        logs = out / 'logs'
        base_sha, base_project = snapshot(repo, request['base'], base, logs, request.get('project_subdir'))
        target_sha, target_project = snapshot(repo, request['target'], target, logs, request.get('project_subdir'))
        result.update(base_commit=base_sha, target_commit=target_sha)

        override = request.get('offline_build')
        restore = None
        if override is not None:
            restore = offline_baseline(target_project, candidate, override)
        try:
            drafted = call('draft', payload(target_project, out / 'draft-build',
                                            candidate=container_path(candidate),
                                            expected_output=request.get('expected_output', '1'),
                                            build_timeout=request.get('build_timeout', 600)),
                           out / 'draft-response.json')
        finally:
            if restore is not None:
                broken, original_bytes, mapping = restore
                broken.write_bytes(original_bytes)
                mapping['restored_broken_sha256'] = digest(broken)
                save(out / 'offline-build-mapping.json', mapping)
        stage('draft', target_sha, drafted)

        base_full = call('buildchecker', payload(base_project, out / 'baseline-full'), out / 'baseline-response.json')
        target_full = call('buildchecker', payload(target_project, out / 'target-full'), out / 'target-response.json')
        stage('full-check', base_sha, {'base': base_full, 'target': target_full})

        increment = call('echecker', payload(target_project, out / 'incremental', base=container_path(base_project),
                                            baseline_graph=container_path(out / 'baseline-full/actual-graph.json'),
                                            target_findings=container_path(out / 'target-full/findings.json'),
                                            target_commit=target_sha), out / 'incremental-response.json')
        stage('incremental-check', target_sha, increment)

        repair = call('mdfixer', payload(target_project, out / 'repair-work',
                                        report=increment['report'], report_sha256=increment['sha256'],
                                        target_commit=target_sha,
                                        expected_output=request.get('expected_output', '1'),
                                        test_command=request.get('test_command')),
                      out / 'repair-response.json')
        stage('repair', target_sha, {'result': repair,
                                    'input_report': {'uri': increment['report'],
                                                     'sha256': increment['sha256']}})

        final = call('buildchecker', payload(target_project, out / 'final-full'), out / 'recheck-response.json')
        missing = [x for x in final['result']['findings'] if x['type'] == 'MISSING']
        if missing:
            raise ValueError(f'Recheck has {len(missing)} missing dependencies')
        stage('recheck', target_sha, {'result': final, 'remaining_missing': 0})
        result['status'] = 'SUCCEEDED'
    except Exception as exc:
        result.update(status='FAILED', error=str(exc))
        if isinstance(exc, ServiceCallError):
            result.update(error_code=exc.error_code, failed_service=exc.role,
                          attempt_count=exc.attempts)
        else:
            result['error_code'] = type(exc).__name__.upper()
    result['artifacts'] = [{'uri': path.relative_to(out).as_posix(), 'sha256': digest(path),
                            'bytes': path.stat().st_size} for path in sorted(out.rglob('*'))
                           if path.is_file() and '.git' not in path.parts and not path.is_symlink()]
    save(out / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = execute(json.loads(args.request.read_text(encoding='utf-8')), args.out.resolve())
    print(json.dumps({'status': result['status'], 'job_id': result['job_id'],
                      'stages': [x['name'] for x in result['stages']],
                      'error_code': result.get('error_code'),
                      'failed_service': result.get('failed_service'),
                      'attempt_count': result.get('attempt_count'),
                      'error': result.get('error')}, ensure_ascii=False))
    return 0 if result['status'] == 'SUCCEEDED' else 1


if __name__ == '__main__':
    sys.exit(main())
