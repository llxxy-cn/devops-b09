import json, tempfile, unittest
from pathlib import Path
from lab import fixture,scan,patch,commit,validate

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'sample';fixture(self.p)

    def test_independent_known_edges(self):
        r=scan(self.p)
        self.assertEqual(r['actual']['main.o'],['config.h','main.c'])
        self.assertEqual({(f['type'],f['dependency']) for f in r['findings']},{('MISSING','config.h'),('REDUNDANT','unused.h')})

    def test_unchanged_reuses_both_targets(self):
        r=scan(self.p,scan(self.p));self.assertEqual(r['reused'],['main.o','helper.o']);self.assertEqual(r['refreshed'],[])

    def test_include_added_invalidates_cache(self):
        old=scan(self.p)
        (self.p/'main.c').write_text('#include "extra.h"\n'+(self.p/'main.c').read_text());commit(self.p,'new include')
        r=scan(self.p,old)
        self.assertIn(['MISSING','main.o','extra.h'],r['added']);self.assertEqual(len(r['refreshed']),2)

    def test_patch_preserves_redundant_dependency(self):
        r=scan(self.p);diff,plan=patch(self.p,r)
        self.assertIn('+main.o: main.c unused.h config.h',diff)
        self.assertNotIn('-\tgcc',diff)
        self.assertNotIn('config.h',(self.p/'Makefile').read_text())

    def test_old_report_rejected(self):
        r=scan(self.p);r['commit']='0'*40
        with self.assertRaisesRegex(ValueError,'STALE_REPORT'):patch(self.p,r)

    def test_unsafe_dependency_rejected(self):
        r=scan(self.p);r['findings']=[{'type':'MISSING','target':'main.o','dependency':'../outside.h'}]
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):patch(self.p,r)

    def test_unsupported_configuration_rejected(self):
        (self.p/'Makefile').write_text((self.p/'Makefile').read_text().replace('-O0','-include unknown.h'))
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_FLAGS'):scan(self.p)

class B3ValidationTests241880556(unittest.TestCase):
    """B3: a build failure rejects the candidate and preserves the source."""

    def test_build_failure_keeps_original_makefile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'sample'
            fixture(project)
            diff, _ = patch(project, scan(project))
            candidate = root / 'candidate.patch'
            candidate.write_text(diff)
            before = (project / 'Makefile').read_bytes()

            (project / 'main.c').write_text('this is invalid C;\n')
            result = validate(project, candidate, root / 'validation')

            self.assertTrue(result['checks']['patch_applies'])
            self.assertFalse(result['checks'].get('build', False))
            self.assertIn('COMMAND_FAILED', result['error'])
            self.assertFalse(result['accepted'])
            self.assertTrue(result['rollback'])
            self.assertTrue(result['source_unchanged'])
            self.assertEqual((project / 'Makefile').read_bytes(), before)

if __name__=='__main__':unittest.main()

class B1InputTests241880481(unittest.TestCase):
    """B1: independent expectations for report inputs and source preservation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name) / 'sample'
        fixture(self.p)
        self.report = scan(self.p)
        self.before = (self.p / 'Makefile').read_bytes()

    def test_redundant_only_produces_no_patch(self):
        self.report['findings'] = [
            {'type': 'REDUNDANT', 'target': 'main.o',
             'dependency': 'unused.h'}
        ]
        diff, plan = patch(self.p, self.report)
        self.assertEqual(diff, '')
        self.assertEqual(plan, [])
        self.assertEqual(
            (self.p / 'Makefile').read_bytes(), self.before
        )

    def test_unknown_target_rejected_without_source_change(self):
        self.report['findings'] = [
            {'type': 'MISSING', 'target': 'unknown.o',
             'dependency': 'config.h'}
        ]
        with self.assertRaisesRegex(ValueError, '^UNSUPPORTED_TARGET$'):
            patch(self.p, self.report)
        self.assertEqual(
            (self.p / 'Makefile').read_bytes(), self.before
        )
