"""Independently verify one successful four-service evidence directory."""

import argparse
import hashlib
import json
from pathlib import Path

STAGES = ('draft', 'full-check', 'incremental-check', 'repair', 'recheck')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify(root):
    root = root.resolve()
    result = read(root / 'result.json')
    assert result['status'] == 'SUCCEEDED', result.get('error')
    assert [stage['name'] for stage in result['stages']] == list(STAGES)
    job, trace = result['job_id'], result['trace_id']
    for stage in result['stages']:
        name, artifact = stage['name'], stage['artifact']
        path = root / (name + '.json')
        assert artifact['uri'] == path.name and sha(path) == artifact['sha256']
        envelope = read(path)
        assert (envelope['job_id'], envelope['trace_id']) == (job, trace)
        assert envelope['status'] == 'SUCCEEDED'
        assert envelope['commit'] == (result['base_commit'] if name == 'full-check'
                                       else result['target_commit'])
    manifest = result['artifacts']
    observed = set()
    for item in manifest:
        path = (root / item['uri']).resolve()
        assert path.is_relative_to(root) and path.is_file()
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
        observed.add(item['uri'])
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and '.git' not in p.parts and not p.is_symlink()
              and p.name != 'result.json'}
    # Inner stage result.json files are part of the manifest.
    actual.update(p.relative_to(root).as_posix() for p in root.rglob('result.json')
                  if p != root / 'result.json' and '.git' not in p.parts)
    assert observed == actual, {'missing': sorted(actual-observed),
                                'extra': sorted(observed-actual)}
    request = read(root / 'request.json')
    assert (result['base_commit'], result['target_commit']) == (request['base'], request['target'])
    report = root / 'incremental/incremental-check.json'
    repair = read(root / 'repair.json')
    assert repair['data']['input_report']['sha256'] == sha(report)
    validation = read(root / 'repair-work/validation/validation.json')
    assert validation['accepted'] and not validation['rollback']
    assert validation['edge_rebuilds'] and all(x['passed'] for x in validation['edge_rebuilds'])
    final = read(root / 'final-full/findings.json')
    assert final['status'] == 'SUCCEEDED'
    assert not any(x['type'] == 'MISSING' for x in final['findings'])
    assert read(root / 'recheck.json')['data']['remaining_missing'] == 0
    if 'offline_build' in request:
        mapping = read(root / 'offline-build-mapping.json')
        assert mapping['original_broken_sha256'] == mapping['restored_broken_sha256']
        assert mapping['original_candidate_sha256'] == request['offline_build']['original_candidate_sha256']
        assert mapping['derived_candidate_sha256'] == request['offline_build']['derived_candidate_sha256']
    draft = read(root / 'draft-build/result.json')
    return {'status': result['status'], 'job_id': job, 'trace_id': trace,
            'base_commit': result['base_commit'], 'target_commit': result['target_commit'],
            'artifact_count': len(manifest), 'result_sha256': sha(root / 'result.json'),
            'incremental_report_sha256': sha(report),
            'candidate_patch_sha256': sha(root / 'repair-work/candidate.patch'),
            'validation_sha256': sha(root / 'repair-work/validation/validation.json'),
            'final_recheck_sha256': sha(root / 'final-full/findings.json'),
            'rebuild_count': len(validation['edge_rebuilds']),
            'remaining_findings': [(x['type'], x['target'], x['dependency'])
                                   for x in final['findings']],
            'candidate_image_id': draft['attempts'][-1]['image_id']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps({str(path): verify(path) for path in args.directories},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
