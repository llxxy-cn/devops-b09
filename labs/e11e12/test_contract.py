import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pipeline
import server

class Contracts(unittest.TestCase):
    def report(self):return {'schema_version':'e11e12-1','kind':'incremental-check','commit':'a'*40,'status':'SUCCEEDED'}
    def source_report(self):
        return {
            'job_id':'job-source',
            'trace_id':'trace-source',
            'uri':'artifact://job-source/incremental-check.json',
            'sha256':'1'*64,
            'bytes':3052,
        }
    def test_accept_current_report(self):pipeline.check_envelope(self.report(),'a'*40,'incremental-check')
    def test_reject_old_commit(self):
        with self.assertRaisesRegex(pipeline.Failure,'another commit'):pipeline.check_envelope(self.report(),'b'*40)
    def test_reject_schema(self):
        r=self.report();r['schema_version']='old'
        with self.assertRaises(pipeline.Failure):pipeline.check_envelope(r,'a'*40)
    def test_reject_failed_upstream(self):
        r=self.report();r['status']='FAILED'
        with self.assertRaises(pipeline.Failure):pipeline.check_envelope(r,'a'*40)
    def test_reject_wrong_artifact_kind(self):
        with self.assertRaises(pipeline.Failure):pipeline.check_envelope(self.report(),'a'*40,'fixed-md')
    def test_artifact_uses_relative_uri_and_content_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'x.json';p.write_text('{}')
            a=pipeline.artifact(p,root,'job-1');self.assertEqual(a['uri'],'artifact://job-1/x.json');self.assertEqual(len(a['sha256']),64)
    def test_existing_evidence_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'keep').write_text('keep')
            with self.assertRaises(pipeline.Failure):pipeline.execute({},root)
            self.assertEqual((root/'keep').read_text(),'keep')
    def test_changed_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json';p.write_text('{}')
            with self.assertRaises(pipeline.Failure):pipeline.load_artifact(p,'0'*64)
    def test_e11_b_fixed_report_accepts_matching_transfer_hash(self):
        with tempfile.TemporaryDirectory() as d:
            report=Path(d)/'fixed.json'
            report.write_text(json.dumps(self.report()))
            request={'fixed_report':str(report),'fixed_report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()}
            loaded=pipeline.load_fixed_report(request)
            self.assertEqual(loaded,self.report())
    def test_e11_b_fixed_report_rejects_changed_transfer_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            report=Path(d)/'fixed.json';report.write_text(json.dumps(self.report())+'\n')
            request={'fixed_report':str(report),'fixed_report_sha256':'0'*64}
            with self.assertRaisesRegex(pipeline.Failure,'Artifact content changed') as caught:
                pipeline.load_fixed_report(request)
            self.assertEqual(caught.exception.code,'ARTIFACT_HASH_MISMATCH')
    def test_e11_b_fixed_report_keeps_legacy_request_compatibility(self):
        with tempfile.TemporaryDirectory() as d:
            report=Path(d)/'fixed.json';report.write_text(json.dumps(self.report()))
            loaded=pipeline.load_fixed_report({'fixed_report':str(report)})
            self.assertEqual(loaded,self.report())
    def test_source_report_identity_accepts_exact_match(self):
        source=self.source_report()
        envelope={'source_report':copy.deepcopy(source)}
        self.assertEqual(pipeline.check_source_report(envelope,source),source)
    def test_source_report_identity_rejects_invalid_expected_fields(self):
        valid=self.source_report()
        invalid=[]
        missing=dict(valid);missing.pop('bytes');invalid.append(missing)
        unknown=dict(valid,unexpected='value');invalid.append(unknown)
        invalid.append('not-an-object')
        invalid.append(dict(valid,sha256='ABC'))
        invalid.append(dict(valid,bytes=0))
        for expected in invalid:
            with self.subTest(expected=expected):
                with self.assertRaises(pipeline.Failure) as caught:
                    pipeline.check_source_report({'source_report':valid},expected)
                self.assertEqual(caught.exception.code,'INVALID_REQUEST')
    def test_source_report_identity_rejects_mismatch(self):
        expected=self.source_report()
        actual=dict(expected,job_id='job-other')
        with self.assertRaises(pipeline.Failure) as caught:
            pipeline.check_source_report({'source_report':actual},expected)
        self.assertEqual(caught.exception.code,'SOURCE_REPORT_MISMATCH')
    def test_project_compat_accepts_minimal_root_make_profile(self):
        request={
            'project_compat':{'layout':'root-make','make_test':False},
            'expected_source_report':self.source_report(),
        }
        self.assertEqual(
            pipeline.parse_project_compat(request,'e11-b'),
            {'layout':'root-make','make_test':False},
        )
    def test_project_compat_rejects_invalid_fields(self):
        source=self.source_report()
        invalid=[
            None,
            {'layout':'root-make'},
            {'make_test':False},
            {'layout':'other','make_test':False},
            {'layout':'root-make','make_test':'false'},
            {'layout':'root-make','make_test':False,'command':'make app'},
        ]
        for compat in invalid:
            with self.subTest(compat=compat):
                request={'project_compat':compat,'expected_source_report':source}
                with self.assertRaises(pipeline.Failure) as caught:
                    pipeline.parse_project_compat(request,'e11-b')
                self.assertEqual(caught.exception.code,'INVALID_REQUEST')
    def test_project_compat_requires_e11_b_and_expected_source(self):
        compat={'layout':'root-make','make_test':False}
        with self.assertRaises(pipeline.Failure) as wrong_mode:
            pipeline.parse_project_compat(
                {'project_compat':compat,'expected_source_report':self.source_report()},
                'e12',
            )
        self.assertEqual(wrong_mode.exception.code,'INVALID_REQUEST')
        with self.assertRaises(pipeline.Failure) as missing_source:
            pipeline.parse_project_compat({'project_compat':compat},'e11-b')
        self.assertEqual(missing_source.exception.code,'INVALID_REQUEST')
    def test_missing_project_compat_keeps_legacy_behavior(self):
        self.assertIsNone(pipeline.parse_project_compat({},'e11-b'))
    def test_same_key_same_request_same_job(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);store=server.Store(root/'jobs')
            request={'mode':'e11-a','repo':str(pipeline.ROOT/'data/p'),'base':'a','target':'b'}
            with patch.object(store.pool,'submit'):
                one=store.submit(request,'same');two=store.submit(request,'same')
                self.assertEqual(one['job_id'],two['job_id'])
                changed=dict(request,target='c')
                with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_CONFLICT'):store.submit(changed,'same')
            store.pool.shutdown()
    def test_api_rejects_repo_outside_data(self):
        with tempfile.TemporaryDirectory() as d:
            store=server.Store(Path(d)/'jobs')
            with self.assertRaises(ValueError):store.submit({'mode':'e11-a','repo':str(Path(d)),'base':'a','target':'b'},'k')
            store.pool.shutdown()

if __name__=='__main__':unittest.main()
