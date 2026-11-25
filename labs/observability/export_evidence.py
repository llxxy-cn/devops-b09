"""Export real Prometheus samples and correlate B3's three-phase task logs."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path('work/b3-observability.QLuAhB')
BASE = 'http://127.0.0.1:19190'
QUERIES = {
    'availability': 'up{job="b09-business"}',
    'calls_started': 'b09_service_tasks_started_total',
    'calls_completed': 'b09_service_tasks_total',
    'calls_active': 'b09_service_tasks_in_progress',
    'success_increase': 'sum by (role) (increase(b09_service_tasks_total{status="SUCCEEDED"}[1m]))',
    'failure_increase': 'sum by (role) (increase(b09_service_tasks_total{status="FAILED"}[1m]))',
    'duration_p95': 'histogram_quantile(0.95, sum by (le, role) (rate(b09_service_task_duration_seconds_bucket[5m])))',
    'duration_mean': 'sum by (role) (rate(b09_service_task_duration_seconds_sum[5m])) / sum by (role) (rate(b09_service_task_duration_seconds_count[5m]))',
}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def timestamp(name):
    return datetime.fromisoformat((ROOT / name).read_text().strip().replace('Z', '+00:00')).timestamp()


def get(path, params=None):
    url = BASE + path
    if params:
        url += '?' + urlencode(params)
    with urlopen(url, timeout=60) as response:
        data = json.loads(response.read())
    if data.get('status') != 'success':
        raise ValueError(data)
    return data


def main():
    output = ROOT / 'observability-export'
    if output.exists():
        raise SystemExit('Export directory exists. Preserve it and inspect the previous result.')
    output.mkdir()
    phases = {}
    identities = set()
    lines = (ROOT / 'three-phase-services.log').read_text(encoding='utf-8').splitlines()
    for phase, expected in [('normal', 'SUCCEEDED'), ('fault', 'FAILED'), ('recovery', 'SUCCEEDED')]:
        result = json.loads((ROOT / (phase + '-01') / 'result.json').read_text())
        assert result['status'] == expected, phase
        identity = (result['job_id'], result['trace_id'])
        assert identity not in identities, phase
        identities.add(identity)
        start = timestamp(phase + '-start-utc.txt')
        end = timestamp(phase + '-end-utc.txt')
        assert end >= start, phase
        events = []
        for line in lines:
            begin = line.find('{')
            if begin < 0:
                continue
            try:
                event = json.loads(line[begin:])
            except json.JSONDecodeError:
                continue
            if (event.get('job_id'), event.get('trace_id')) == identity:
                events.append(event)
        roles = sorted({event['role'] for event in events if 'role' in event})
        assert {'draft', 'buildchecker'} <= set(roles), (phase, roles)
        if phase != 'fault':
            assert {'echecker', 'mdfixer'} <= set(roles), (phase, roles)
        save(output / (phase + '-correlated-logs.json'), events)
        phases[phase] = {'job_id': identity[0], 'trace_id': identity[1],
                         'status': result['status'], 'error': result.get('error'),
                         'start_epoch': start, 'end_epoch': end,
                         'roles_observed': roles, 'log_events': len(events)}
        print('LOG_CORRELATION_PASS', phase, roles)
    start = phases['normal']['start_epoch'] - 60
    end = max(phases['recovery']['end_epoch'] + 30, datetime.now(timezone.utc).timestamp())
    step = max(5, math.ceil((end - start) / 10000))
    windows = {'full': (start, end, step)}
    for phase, record in phases.items():
        windows[phase] = (record['start_epoch'] - 60, record['end_epoch'] + 60, 5)
    links = []
    for window, (left, right, interval) in windows.items():
        right = min(right, datetime.now(timezone.utc).timestamp())
        for name, query in QUERIES.items():
            result = get('/api/v1/query_range', {'query': query, 'start': left, 'end': right, 'step': interval})
            save(output / window / (name + '.json'), result)
        args = urlencode({'orgId': 1, 'from': int(left * 1000), 'to': int(right * 1000), 'timezone': 'utc'})
        links.append(window + '\nhttp://127.0.0.1:13100/d/b09-microservice?' + args)
    targets = get('/api/v1/targets')
    save(output / 'targets-after-recovery.json', targets)
    active = targets['data']['activeTargets']
    assert len(active) == 4 and all(t['health'] == 'up' for t in active)
    fault = json.loads((output / 'fault' / 'availability.json').read_text())
    down = any(series['metric'].get('service') == 'echecker' and any(float(v) == 0 for _, v in series['values'])
               for series in fault['data']['result'])
    assert down, 'Fault window has no stored EChecker up=0 sample'
    recovered = get('/api/v1/query', {'query': 'up{job="b09-business",service="echecker"}'})
    save(output / 'echecker-recovered.json', recovered)
    assert recovered['data']['result'] and all(float(s['value'][1]) == 1 for s in recovered['data']['result'])
    with urlopen('http://127.0.0.1:13100/api/dashboards/uid/b09-microservice', timeout=10) as response:
        save(output / 'grafana-dashboard-export.json', json.loads(response.read()))
    save(output / 'three-phase-summary.json', {'phases': phases, 'queries': QUERIES,
        'full_window_step_seconds': step, 'fault_down_sample_verified': True,
        'current_four_targets_up': True,
        'metric_unit': 'service invocation; complete pipeline task counts come from result.json'})
    (output / 'grafana-links.txt').write_bytes(('\n\n'.join(links) + '\n').encode())
    print('THREE_PHASE_EXPORT_PASS')
    print('OUTPUT', output)
    print('GRAFANA_LINKS\n' + '\n\n'.join(links))


if __name__ == '__main__':
    main()
