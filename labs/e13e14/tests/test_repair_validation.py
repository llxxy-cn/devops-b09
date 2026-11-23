"""Regression for the H1 case: the repaired header need not be config.h."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'labs/e8e10'), str(ROOT / 'labs/e13e14')]
from lab import commit, fixture, patch, scan
from repair_validation import validate_repair


@unittest.skipUnless(all(shutil.which(name) for name in ('git', 'make', 'gcc')),
                     'requires Git, GNU Make and GCC')
class RepairValidationTests(unittest.TestCase):
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
