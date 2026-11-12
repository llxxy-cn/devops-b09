"""Exercise the E12 API and save independently verified evidence."""

import argparse
import hashlib
import json
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


STAGES = ('draft', 'full-check', 'incremental-check', 'repair', 'recheck')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def call(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def preflight(url, request, out, timeout):
    require(request.get('mode') == 'e12', 'Expected a mode=e12 request')
    out.mkdir(parents=True)

    def json_call(path, filename, status=200, body=None):
        code, _, data = call(url + path, body)
        (out / filename).write_bytes(data)
        require(code == status, f'{path}: expected HTTP {status}, received {code}')
        return json.loads(data)

    json_call('/health', 'health.json')
    submission = {'idempotency_key': 'e12-b3-' + uuid.uuid4().hex, 'input': request}
    (out / 'submission.json').write_text(json.dumps(submission, indent=2), encoding='utf-8')
    first = json_call('/v1/jobs', 'submit.json', 202, submission)
    job_id = first['job_id']
    replay = json_call('/v1/jobs', 'replay.json', 202, submission)
    require(replay['job_id'] == job_id, 'Replay created another job')
    changed = dict(submission, input=dict(request, target=request['base']))
    require(changed != submission, 'Conflict test requires distinct base and target')
    conflict = json_call('/v1/jobs', 'conflict.json', 409, changed)
    require(conflict.get('error') == 'IDEMPOTENCY_CONFLICT', 'Unexpected conflict response')

    job = '/v1/jobs/' + quote(job_id, safe='')
    deadline = time.monotonic() + timeout
    with (out / 'poll.jsonl').open('w', encoding='utf-8') as polls:
        while True:
            state = json_call(job, 'state.json')
            polls.write(json.dumps(state) + '\n')
            polls.flush()
            if state['status'] not in ('QUEUED', 'RUNNING'):
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(f'Polling expired for {job_id}')
            time.sleep(3)

    result = json_call(job + '/artifacts', 'result.json')
    require(state['status'] == result['status'] == 'SUCCEEDED', f'{job_id}: {result.get("error")}')
    require(result['job_id'] == job_id, 'Manifest belongs to another job')
    require(state['trace_id'] == result['trace_id'], 'State and manifest trace IDs differ')
    for field in ('base', 'target'):
        if len(request[field]) == 40:
            require(result[field + '_commit'] == request[field], f'{field}: requested SHA differs')
    require([stage['name'] for stage in result['stages']] == list(STAGES), 'Unexpected stage sequence')
    prefix = f'artifact://{job_id}/'
    manifest = {entry['uri']: entry for entry in result['artifacts']}
    verified = {}

    def download(name):
        entry = manifest[prefix + name]
        code, headers, data = call(job + '/files/' + quote(name, safe='/'))
        require(code == 200, f'{name}: download returned HTTP {code}')
        digest = hashlib.sha256(data).hexdigest()
        require(digest == entry['sha256'] == headers.get('X-Content-SHA256'), f'{name}: SHA256 mismatch')
        require(len(data) == entry['bytes'], f'{name}: byte count mismatch')
        path = out / 'downloads' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        verified[name] = digest
        return data

    stages = {}
    for stage in result['stages']:
        name = stage['name']
        filename = name + '.json'
        require(stage['artifact'] == manifest[prefix + filename], f'{name}: stage manifest differs')
        envelope = json.loads(download(filename))
        require(envelope['kind'] == name and envelope['status'] == 'SUCCEEDED', f'{name}: wrong envelope')
        require(envelope['job_id'] == job_id and envelope['trace_id'] == result['trace_id'], f'{name}: wrong job')
        commit = result['base_commit'] if name == 'full-check' else result['target_commit']
        require(envelope['commit'] == commit, f'{name}: wrong commit')
        stages[name] = envelope['data']
    download('candidate.patch')
    require(stages['repair']['input_report'] == manifest[prefix + 'incremental-check.json'],
            'Repair did not consume this job’s incremental report')
    if 'expected_missing' in request:
        expected = {(item['target'], item['dependency']) for item in request['expected_missing']}
        observed = {(item['target'], item['dependency']) for item in stages['incremental-check']['findings']
                    if item['type'] == 'MISSING'}
        repaired = {(item['target'], item['dependency']) for item in stages['repair']['edits']}
        require(observed == expected == repaired, 'Observed or repaired MD differs from the handoff')
    image_id = result['image_id']
    require(image_id == stages['draft']['attempts'][-1]['image_id']
            == stages['incremental-check']['image_id']
            == stages['recheck']['validation']['image_id'], 'DRAFT image differs across stages')
    require(stages['recheck']['validation']['accepted'], 'Candidate was rejected')
    require(not any(f['type'] == 'MISSING' for f in stages['recheck']['findings']), 'Recheck still reports MD')
    image_logs = [
        json.loads(download(uri.removeprefix(prefix)))
        for uri in sorted(manifest) if uri.startswith(prefix + 'image-execution/') and uri.endswith('.json')
    ]
    require(image_logs and all(log['image_id'] == image_id and log['status'] == 'SUCCEEDED'
                              for log in image_logs), 'Missing or invalid image execution records')
    require({'gcc', 'make', './app'} <= {log['command'][log['command'].index('--entrypoint') + 1]
                                        for log in image_logs}, 'Incomplete image execution records')
    summary = {'status': 'SUCCEEDED', 'job_id': job_id, 'trace_id': result['trace_id'],
               'image_id': image_id, 'same_key_same_job': True, 'conflict_http_status': 409,
               'stages': list(STAGES), 'verified_sha256': verified}
    (out / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--url', default='http://127.0.0.1:8080')
    parser.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args()
    preflight(args.url.rstrip('/'), json.loads(args.request.read_text(encoding='utf-8')), args.out, args.timeout)
