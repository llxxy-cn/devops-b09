"""Regression for the H1 case: the repaired header need not be config.h."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'labs/e8e10'), str(ROOT / 'labs/e11e12'),
                str(ROOT / 'labs/e13e14')]
from lab import commit, fixture, patch, scan
from pipeline import Failure, validate_in_draft
from repair_validation import validate_repair


class LocalRuntime:
    """Exercise the E12 validation branch without a Docker daemon."""

    image_id = 'sha256:' + '0' * 64

    def run(self, argv, project):
        result = subprocess.run(argv, cwd=project, capture_output=True, text=True,
                                check=True, timeout=30)
        return result.stdout.strip()

    def scan(self, project, *, real=False):
        return scan(project)


@unittest.skipUnless(all(shutil.which(name) for name in ('git', 'make', 'gcc')),
                     'requires Git, GNU Make and GCC')
class RepairValidationTests(unittest.TestCase):
    def test_e12_h1_repair_accepts_extra_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            fixture(project)
            main = project / 'main.c'
            main.write_text(main.read_text().replace('#include "config.h"',
                                                    '#include "config.h"\n#include "extra.h"')
                            .replace('VALUE+helper()', 'VALUE+EXTRA+helper()'))
            makefile = project / 'Makefile'
            makefile.write_text(makefile.read_text().replace('main.c unused.h',
                                                            'main.c config.h'))
            commit(project, 'H1 extra header use')
            before_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                 cwd=project, text=True).strip()
            diff, edits = patch(project, scan(project))
            self.assertEqual([(e['target'], e['dependency']) for e in edits],
                             [('main.o', 'extra.h')])
            candidate = root / 'candidate.patch'
            candidate.write_text(diff)
            verdict, sandbox = validate_in_draft(project, candidate, edits,
                                                 root / 'e12-validation',
                                                 LocalRuntime(), '1', False)
            self.assertTrue(verdict['accepted'], verdict)
            rebuilds = (root / 'e12-validation' / 'edge-rebuilds.json').read_text()
            self.assertIn('extra.h', rebuilds)
            self.assertIn('extra.h', (sandbox / 'Makefile').read_text())
            self.assertNotIn('extra.h', makefile.read_text())
            self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                     cwd=project, text=True).strip(), before_sha)

    def test_e12_bad_patch_preserves_source_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            fixture(project)
            before_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                 cwd=project, text=True).strip()
            before = (project / 'Makefile').read_bytes()
            candidate = root / 'bad.patch'
            candidate.write_text('not a patch\n')
            with self.assertRaises(Failure):
                validate_in_draft(project, candidate,
                                  [{'target': 'main.o', 'dependency': 'extra.h'}],
                                  root / 'e12-validation', LocalRuntime(), '1', False)
            self.assertEqual((project / 'Makefile').read_bytes(), before)
            self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                     cwd=project, text=True).strip(), before_sha)

    def test_repaired_extra_header_rebuilds_without_config_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            fixture(project)
            main = project / 'main.c'
            main.write_text(main.read_text().replace('#include "config.h"',
                                                    '#include "config.h"\n#include "extra.h"')
                            .replace('VALUE+helper()', 'VALUE+EXTRA+helper()'))
            makefile = project / 'Makefile'
            makefile.write_text(makefile.read_text().replace('main.c unused.h', 'main.c config.h'))
            commit(project, 'C1 extra header use')
            report = scan(project)
            diff, edits = patch(project, report)
            self.assertEqual([(e['target'], e['dependency']) for e in edits],
                             [('main.o', 'extra.h')])
            candidate = root / 'candidate.patch'
            candidate.write_text(diff)
            verdict = validate_repair(project, candidate, edits, root / 'validation', '1')
            self.assertTrue(verdict['accepted'], verdict)
            self.assertTrue(verdict['checks']['edge_rebuilds'])
            self.assertIn('extra.h', makefile.read_text())

    def test_bad_patch_is_rejected_without_changing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            fixture(project)
            before = (project / 'Makefile').read_bytes()
            candidate = root / 'candidate.patch'
            candidate.write_text('not a patch\n')
            verdict = validate_repair(project, candidate,
                                      [{'target': 'main.o', 'dependency': 'config.h'}],
                                      root / 'validation', '1')
            self.assertFalse(verdict['accepted'])
            self.assertTrue(verdict['rollback'])
            self.assertEqual((project / 'Makefile').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
