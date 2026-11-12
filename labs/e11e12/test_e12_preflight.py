import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline
from lab import commit, fixture


class E12PreflightTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix', 'Snapshot integration runs on the Linux course host')
    def test_snapshot_keeps_commit_identity_in_project_subdirectory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / 'repo'
            fixture(repo)
            project = repo / 'fixtures' / 'real'
            project.mkdir(parents=True)
            for name in ('main.c', 'helper.c', 'config.h', 'Makefile'):
                (project / name).write_bytes((repo / name).read_bytes())
            sha = commit(repo, 'add nested C project')
            result, snapshot = pipeline.snapshot(
                repo, sha, root / 'snapshot', root / 'logs', 'fixtures/real'
            )
            self.assertEqual(result, sha)
            self.assertEqual(snapshot, root / 'snapshot' / 'fixtures' / 'real')
            self.assertEqual(pipeline.scan(snapshot)['commit'], sha)

    def test_project_subdir_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = pipeline.execute(
                {'mode': 'e12', 'repo': str(root), 'project_subdir': '../outside'},
                root / 'output',
            )
            self.assertEqual(result['error']['code'], 'INVALID_REQUEST')

    def test_runtime_runs_exact_candidate_with_only_project_bind(self):
        image_id = 'sha256:' + 'a' * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            project = root / 'work' / 'project'
            project.mkdir(parents=True)
            with patch.object(pipeline, 'ROOT', root), \
                 patch.dict(os.environ, {'COURSE_HOST_ROOT': str(root / 'host')}), \
                 patch.object(os, 'getuid', return_value=1001, create=True), \
                 patch.object(os, 'getgid', return_value=1001, create=True), \
                 patch.object(pipeline, 'command', return_value='hello E3') as run:
                runtime = pipeline.DraftRuntime(image_id, root / 'logs')
                self.assertEqual(runtime.run(['./app'], project), 'hello E3')
            argv = run.call_args.args[0]
            self.assertEqual(argv[-3:], ['--entrypoint', './app', image_id])
            self.assertIn(f'type=bind,source={root / "host" / "work" / "project"},target=/project', argv)
            self.assertNotIn('/var/run/docker.sock', ' '.join(argv))
            record = json.loads((root / 'logs/001.json').read_text())
            self.assertEqual(record['image_id'], image_id)
            self.assertEqual(record['status'], 'SUCCEEDED')
