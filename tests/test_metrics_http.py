"""Exercise the actual HTTP handler without executing project builds."""

import ast
import importlib.util
import json
import sys
import threading
import time
import traceback
import unittest
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / 'labs/e13e14'
sys.path.insert(0, str(SERVICE))
from service_metrics import ServiceBusy, ServiceMetrics


class MetricsHTTPTests(unittest.TestCase):
    def setUp(self):
        self.entered = threading.Event()
        self.release = threading.Event()

        def run(data):
            if data.get('block'):
                self.entered.set()
                if not self.release.wait(5):
                    raise TimeoutError('test release expired')
            if data.get('fail'):
                raise ValueError('TIMED_OUT test')
            return {'status': 'SUCCEEDED'}

        namespace = dict(BaseHTTPRequestHandler=BaseHTTPRequestHandler,
                         json=json, time=time, traceback=traceback,
                         datetime=datetime, timezone=timezone, ROLE='echecker',
                         METRICS=ServiceMetrics('echecker'),
                         RUN_LOCK=threading.Lock(), ServiceBusy=ServiceBusy, run=run)
        tree = ast.parse((SERVICE / 'service.py').read_text(encoding='utf-8'))
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Handler')
        exec(compile(ast.Module(body=[handler], type_ignores=[]), 'service-handler', 'exec'), namespace)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), namespace['Handler'])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def get(self, path):
        with urlopen(self.url + path, timeout=2) as response:
            return response.read().decode()

    def post(self, data):
        request = Request(self.url + '/v1/run', json.dumps(data).encode(),
                          {'Content-Type': 'application/json'})
        try:
            response = urlopen(request, timeout=8)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def test_metrics_remain_available_during_work_and_busy_is_bounded(self):
        replies = []
        worker = threading.Thread(target=lambda: replies.append(self.post({'block': True})))
        worker.start()
        try:
            self.assertTrue(self.entered.wait(2))
            text = self.get('/metrics')
            self.assertIn('b09_service_tasks_in_progress{role="echecker"} 1', text)
            self.assertEqual(json.loads(self.get('/health'))['status'], 'ok')
            code, result = self.post({})
            self.assertEqual((code, result['error_code']), (503, 'SERVICE_BUSY'))
        finally:
            self.release.set()
            worker.join(timeout=3)
        self.assertEqual(replies[0][0], 200)
        text = self.get('/metrics')
        self.assertIn('status="SUCCEEDED"} 1', text)
        self.assertIn('status="FAILED"} 1', text)
        self.assertIn('b09_service_tasks_in_progress{role="echecker"} 0', text)
        self.assertIn('le="+Inf"} 2', text)

    def test_error_and_malformed_body_are_counted_and_recovery_succeeds(self):
        self.assertEqual(self.post({'fail': True})[0], 422)
        self.assertEqual(self.post([])[0], 422)
        self.assertEqual(self.post({})[0], 200)
        text = self.get('/metrics')
        self.assertIn('status="FAILED"} 2', text)
        self.assertIn('status="SUCCEEDED"} 1', text)
        self.assertIn('le="+Inf"} 3', text)


if __name__ == '__main__':
    unittest.main()
