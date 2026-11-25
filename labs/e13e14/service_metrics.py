"""Process-local Prometheus counters for real /v1/run service calls."""

import json
import threading


class ServiceBusy(Exception):
    """A worker is already using this service's build workspace."""


class ServiceMetrics:
    BUCKETS = (0.01, 0.1, 0.5, 1, 5, 15, 60, 300, 900, 1800)

    def __init__(self, role):
        self.role = role
        self.lock = threading.Lock()
        self.started = 0
        self.active = 0
        self.completed = {'SUCCEEDED': 0, 'FAILED': 0}
        self.buckets = [0] * len(self.BUCKETS)
        self.duration_sum = 0.0

    def start(self):
        with self.lock:
            self.started += 1
            self.active += 1

    def finish(self, status, seconds):
        with self.lock:
            self.active -= 1
            self.completed[status] += 1
            self.duration_sum += seconds
            for index, boundary in enumerate(self.BUCKETS):
                if seconds <= boundary:
                    self.buckets[index] += 1

    def render(self):
        role = 'role=' + json.dumps(self.role)
        with self.lock:
            count = sum(self.completed.values())
            lines = [
                '# HELP b09_service_tasks_started_total Calls received at /v1/run.',
                '# TYPE b09_service_tasks_started_total counter',
                f'b09_service_tasks_started_total{{{role}}} {self.started}',
                '# HELP b09_service_tasks_in_progress Calls currently being handled.',
                '# TYPE b09_service_tasks_in_progress gauge',
                f'b09_service_tasks_in_progress{{{role}}} {self.active}',
                '# HELP b09_service_tasks_total Completed service calls by outcome.',
                '# TYPE b09_service_tasks_total counter',
            ]
            for status, value in self.completed.items():
                lines.append(f'b09_service_tasks_total{{{role},status="{status}"}} {value}')
            lines += [
                '# HELP b09_service_task_duration_seconds Service call handling duration.',
                '# TYPE b09_service_task_duration_seconds histogram',
            ]
            for boundary, value in zip(self.BUCKETS, self.buckets):
                lines.append(f'b09_service_task_duration_seconds_bucket{{{role},le="{boundary}"}} {value}')
            lines += [
                f'b09_service_task_duration_seconds_bucket{{{role},le="+Inf"}} {count}',
                f'b09_service_task_duration_seconds_sum{{{role}}} {self.duration_sum}',
                f'b09_service_task_duration_seconds_count{{{role}}} {count}',
            ]
        return '\n'.join(lines) + '\n'
