"""One HTTP boundary per E14 teaching capability, using the existing implementations."""
import hashlib
import json
import os
import sys
import time
import traceback
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path[:0] = ['/course/labs/e8e10', '/course/labs/e11e12/vendor', '/app']
from lab import scan, patch
from draft.autobuild import auto_build
from buildchecker.fullcheck import full_check
from repair_validation import compiler_flags, validate_repair

from service_metrics import ServiceBusy, ServiceMetrics

ROOT = Path('/course').resolve()
ROLE = os.environ['E14_ROLE']
METRICS = ServiceMetrics(ROLE)
RUN_LOCK = threading.Lock()


def local(value, area='work'):
    path = Path(value).resolve()
    allowed = ROOT / area
    if not path.is_relative_to(allowed):
        raise ValueError(f'Path must be inside {allowed}')
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(data):
    project = local(data['project'])
    out = local(data['out'])
    if out.exists():
        raise ValueError('Output already exists')
    if ROLE == 'draft':
        candidate = local(data['candidate'], 'data')
        result = auto_build(project, candidate, out, data.get('expected_output', '1'),
                            timeout=float(data.get('build_timeout', 600)))
        if result['status'] != 'SUCCEEDED':
            raise ValueError('DRAFT_' + result['status'] + ': ' + str(result.get('error')))
        return {'status': 'SUCCEEDED', 'result': result, 'artifact': str(out / 'result.json')}
    if ROLE == 'buildchecker':
        result = full_check(project, out)
        if result['status'] != 'SUCCEEDED':
            raise ValueError('BUILDCHECKER_' + result['status'] + ': ' + str(result.get('error')))
        return {'status': 'SUCCEEDED', 'result': result, 'artifact': str(out / 'findings.json')}
    if ROLE == 'echecker':
        base = local(data['base'])
        baseline_graph = local(data['baseline_graph'])
        target_findings = local(data['target_findings'])
        base_flags = compiler_flags(base)
        target_flags = compiler_flags(project)
        old = scan(base, compiler_flags=base_flags)
        graph = json.loads(baseline_graph.read_text())
        projected = {t: sorted({e['dependency'] for e in graph if e['target'] == t})
                     for t in ('main.o', 'helper.o')}
        if old['actual'] != projected:
            raise ValueError('Baseline BuildChecker/GCC graph mismatch')
        old['actual'] = projected
        current = scan(project, old, compiler_flags=target_flags)
        reference = json.loads(target_findings.read_text())
        normalize = lambda fs: sorted((x['type'], x['target'], x['dependency']) for x in fs
                                      if x['target'] in ('main.o', 'helper.o'))
        if reference['status'] != 'SUCCEEDED' or normalize(current['findings']) != normalize(reference['findings']):
            raise ValueError('Incremental/full findings mismatch')
        out.mkdir(parents=True)
        save(out / 'compiler-flags.json', {'base': base_flags, 'target': target_flags})
        save(out / 'baseline-cache.json', old)
        envelope = {'schema_version': 'e11e12-1', 'kind': 'incremental-check',
                    'status': 'SUCCEEDED', 'commit': data['target_commit'],
                    'job_id': data['job_id'], 'trace_id': data['trace_id'], 'data': current}
        if current['commit'] != data['target_commit']:
            raise ValueError('Target commit mismatch')
        save(out / 'incremental-check.json', envelope)
        return {'status': 'SUCCEEDED', 'report': str(out / 'incremental-check.json'),
                'sha256': sha(out / 'incremental-check.json'), 'findings': current['findings']}
    if ROLE == 'mdfixer':
        report = local(data['report'])
        if sha(report) != data['report_sha256']:
            raise ValueError('Report transfer hash mismatch')
        envelope = json.loads(report.read_text())
        if (envelope['schema_version'], envelope['kind'], envelope['status'],
            envelope['commit'], envelope['job_id'], envelope['trace_id'],
            envelope['data']['commit']) != (
                'e11e12-1', 'incremental-check', 'SUCCEEDED', data['target_commit'],
                data['job_id'], data['trace_id'], data['target_commit']):
            raise ValueError('Report identity mismatch')
        out.mkdir(parents=True)
        diff, edits = patch(project, envelope['data'])
        if not diff:
            raise ValueError('No missing dependency to repair')
        candidate = out / 'candidate.patch'
        candidate.write_text(diff, encoding='utf-8')
        save(out / 'repair-plan.json', edits)
        verdict = validate_repair(project, candidate, edits, out / 'validation',
                                  data.get('expected_output', '1'), data.get('test_command'))
        if not verdict['accepted']:
            raise ValueError('Patch rejected: ' + str(verdict))
        return {'status': 'SUCCEEDED', 'patch': str(candidate),
                'sha256': sha(candidate), 'validation': verdict}
    raise ValueError('Unknown role')


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        body = (json.dumps(data, ensure_ascii=False) + '\n').encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/metrics':
            body = METRICS.render().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/health':
            self.reply(200, {'status': 'ok', 'role': ROLE})
        else:
            self.reply(404, {'error': 'NOT_FOUND'})

    def do_POST(self):
        if self.path != '/v1/run':
            self.reply(404, {'error': 'NOT_FOUND'})
            return
        start = time.monotonic()
        METRICS.start()
        data = {}
        status = 'FAILED'
        acquired = False
        response_code = 422
        error_code = None
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 1 or length > 100000:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                data = {}
                raise ValueError('Expected a JSON object')
            acquired = RUN_LOCK.acquire(blocking=False)
            if not acquired:
                raise ServiceBusy('Another service call is running')
            print(json.dumps({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'role': ROLE, 'job_id': data.get('job_id'),
                'trace_id': data.get('trace_id'), 'status': 'RUNNING',
            }), flush=True)
            result = run(data)
            status = 'SUCCEEDED'
            response_code = 200
        except Exception as exc:
            traceback.print_exc()
            error_code = 'TIMEOUT' if 'TIMED_OUT' in str(exc) else type(exc).__name__.upper()
            if isinstance(exc, ServiceBusy):
                error_code = 'SERVICE_BUSY'
                response_code = 503
            result = {'status': 'FAILED', 'role': ROLE,
                      'error_code': error_code, 'error': str(exc)}
        finally:
            if acquired:
                RUN_LOCK.release()
            elapsed = time.monotonic() - start
            METRICS.finish(status, elapsed)
        print(json.dumps({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'role': ROLE, 'job_id': data.get('job_id'),
            'trace_id': data.get('trace_id'), 'status': status,
            'error_code': error_code, 'elapsed_ms': round(elapsed * 1000),
        }), flush=True)
        self.reply(response_code, result)


if __name__ == '__main__':
    if ROLE not in {'draft', 'buildchecker', 'echecker', 'mdfixer'}:
        raise SystemExit('Invalid E14_ROLE')
    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
