"""Check bounded retries and terminal errors for E14 service calls."""

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch


SERVICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE))
import orchestrate


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def succeeded():
    return Response(b'{"status":"SUCCEEDED"}')


def http_error(status, code):
    body = json.dumps({'status': 'FAILED', 'error_code': code}).encode()
    return urllib.error.HTTPError('http://test/v1/run', status, code, {}, io.BytesIO(body))


class ServiceCallRetryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.evidence = Path(self.folder.name) / 'response.json'
        self.attempt_log = Path(self.folder.name) / 'response-attempts.json'

    def call(self):
        return orchestrate.call('echecker', {'job_id': 'job-test'}, self.evidence)

    @patch.object(orchestrate.time, 'sleep')
    @patch.object(orchestrate.urllib.request, 'urlopen')
    def test_connection_refused_recovers_within_three_attempts(self, urlopen, sleep):
        refused = urllib.error.URLError(ConnectionRefusedError('Connection refused'))
        urlopen.side_effect = [refused, refused, succeeded()]
        self.assertEqual(self.call()['status'], 'SUCCEEDED')
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(len(json.loads(self.attempt_log.read_text())), 3)

    @patch.object(orchestrate.time, 'sleep')
    @patch.object(orchestrate.urllib.request, 'urlopen')
    def test_connection_refused_has_terminal_code_and_limit(self, urlopen, sleep):
        urlopen.side_effect = urllib.error.URLError(ConnectionRefusedError('Connection refused'))
        with self.assertRaises(orchestrate.ServiceCallError) as raised:
            self.call()
        self.assertEqual((raised.exception.error_code, raised.exception.attempts),
                         ('DOWNSTREAM_UNAVAILABLE', 3))
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(len(json.loads(self.attempt_log.read_text())), 3)
        self.assertEqual(json.loads(self.evidence.read_text())['error_code'], 'DOWNSTREAM_UNAVAILABLE')

    @patch.object(orchestrate.time, 'sleep')
    @patch.object(orchestrate.urllib.request, 'urlopen')
    def test_busy_response_retries_but_timeout_response_does_not(self, urlopen, sleep):
        urlopen.side_effect = [http_error(503, 'SERVICE_BUSY'), succeeded()]
        self.assertEqual(self.call()['status'], 'SUCCEEDED')
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(sleep.call_count, 1)
        self.evidence.unlink()
        self.attempt_log.unlink()
        urlopen.reset_mock()
        sleep.reset_mock()
        urlopen.side_effect = http_error(422, 'TIMEOUT')
        with self.assertRaises(orchestrate.ServiceCallError) as raised:
            self.call()
        self.assertEqual((raised.exception.error_code, raised.exception.attempts), ('TIMEOUT', 1))
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()

    def test_execute_records_failed_terminal_state(self):
        root = Path(self.folder.name)
        (root / 'data').mkdir()
        (root / 'work').mkdir()
        out = root / 'work/run'
        request = {'repo': '/course/data/repo', 'candidate': '/course/data/candidate',
                   'base': 'a' * 40, 'target': 'b' * 40}
        snapshots = [(request['base'], out / 'base-project'),
                     (request['target'], out / 'target-project')]
        failure = orchestrate.ServiceCallError('draft', 'DOWNSTREAM_UNAVAILABLE', 3,
                                               'Connection refused')
        with patch.object(orchestrate, 'ROOT', root), \
             patch.object(orchestrate, 'snapshot', side_effect=snapshots), \
             patch.object(orchestrate, 'call', side_effect=failure):
            result = orchestrate.execute(request, out)
        self.assertEqual((result['status'], result['error_code'],
                          result['failed_service'], result['attempt_count']),
                         ('FAILED', 'DOWNSTREAM_UNAVAILABLE', 'draft', 3))
        self.assertEqual(json.loads((out / 'result.json').read_text())['status'], 'FAILED')


if __name__ == '__main__':
    unittest.main()
