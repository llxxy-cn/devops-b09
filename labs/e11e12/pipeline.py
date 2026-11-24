"""Compose the existing E5-E10 teaching components using versioned artifacts."""
import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'labs/e8e10'), str(ROOT / 'labs/e11e12/vendor'), '/app']
from lab import scan, patch, validate

class Failure(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def artifact(path, out, job_id):
    return {'uri': f'artifact://{job_id}/{path.relative_to(out).as_posix()}',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes':path.stat().st_size}

def check_envelope(report, commit, kind=None):
    if report.get('schema_version') != 'e11e12-1':
        raise Failure('SCHEMA_MISMATCH', 'Expected e11e12-1')
    if report.get('commit') != commit:
        raise Failure('STALE_REPORT', 'Report belongs to another commit')
    if report.get('status') != 'SUCCEEDED':
        raise Failure('UPSTREAM_FAILED', 'Upstream stage did not succeed')
    if kind and report.get('kind') != kind:
        raise Failure('ARTIFACT_TYPE_MISMATCH', kind)

def load_artifact(path, expected_sha256):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise Failure('ARTIFACT_HASH_MISMATCH','Artifact content changed during transfer')
    return json.loads(data)

def load_fixed_report(request):
    path=Path(request['fixed_report'])
    expected_sha256=request.get('fixed_report_sha256')
    if expected_sha256 is None:
        return json.loads(path.read_text(encoding='utf-8'))
    return load_artifact(path,expected_sha256)

def validate_expected_source_report(expected):
    fields={'job_id','trace_id','uri','sha256','bytes'}
    if not isinstance(expected,dict) or set(expected)!=fields:
        raise Failure('INVALID_REQUEST','expected_source_report must contain exactly the required fields')
    if not all(isinstance(expected[name],str) and expected[name] for name in ('job_id','trace_id','uri')):
        raise Failure('INVALID_REQUEST','Source report identity fields must be non-empty strings')
    if not re.fullmatch(r'[0-9a-f]{64}',expected['sha256']):
        raise Failure('INVALID_REQUEST','Source report SHA256 must be lowercase hexadecimal')
    if not isinstance(expected['bytes'],int) or isinstance(expected['bytes'],bool) or expected['bytes']<=0:
        raise Failure('INVALID_REQUEST','Source report bytes must be a positive integer')
    if not expected['uri'].startswith(f"artifact://{expected['job_id']}/"):
        raise Failure('INVALID_REQUEST','Source report URI must belong to its job')
    return expected

def check_source_report(envelope, expected):
    validate_expected_source_report(expected)
    actual=envelope.get('source_report')
    if actual!=expected:
        raise Failure('SOURCE_REPORT_MISMATCH','Fixed report provenance does not match the requested source')
    return actual

def parse_offline_build(request, mode):
    if 'offline_build' not in request:
        return None
    if mode != 'e11-b':
        raise Failure('INVALID_REQUEST', 'offline_build requires mode=e11-b')
    value = request['offline_build']
    if not isinstance(value, dict) or set(value) != {'base_image', 'make_path'}:
        raise Failure('INVALID_REQUEST', 'offline_build must contain exactly base_image and make_path')
    if not isinstance(value['base_image'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9_.-]*:[a-z0-9][a-z0-9_.-]*', value['base_image']):
        raise Failure('INVALID_REQUEST', 'offline_build base_image must be a local tag')
    if value['make_path'] != '/opt/offline-toolchain/make':
        raise Failure('INVALID_REQUEST', 'Unsupported offline make path')
    return dict(value)

def parse_project_compat(request, mode):
    if 'project_compat' not in request:
        return None
    compat=request['project_compat']
    if mode!='e11-b':
        raise Failure('INVALID_REQUEST','project_compat requires mode=e11-b')
    if not isinstance(compat,dict) or set(compat)!={'layout','make_test'}:
        raise Failure('INVALID_REQUEST','project_compat must contain exactly layout and make_test')
    if compat['layout']!='root-make' or not isinstance(compat['make_test'],bool):
        raise Failure('INVALID_REQUEST','Unsupported project_compat values')
    if 'expected_source_report' not in request:
        raise Failure('INVALID_REQUEST','project_compat requires expected_source_report')
    validate_expected_source_report(request['expected_source_report'])
    if not re.fullmatch(r'[0-9a-f]{64}',request.get('fixed_report_sha256','')):
        raise Failure('INVALID_REQUEST','project_compat requires a lowercase fixed_report_sha256')
    return dict(compat)

def repair_from_artifact(project, report_path, expected_sha256, kind, output):
    report = load_artifact(report_path, expected_sha256)
    target = subprocess.check_output(
        ['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True
    ).strip()
    check_envelope(report, target, kind)
    data = report['data']
    if data['commit'] != target:
        raise Failure('STALE_REPORT', 'Report data belongs to another commit')
    diff, edits = patch(project, data)
    if not diff:
        raise Failure('NO_MISSING_DEPENDENCY', 'No MD to repair')
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(diff)
    return edits

def command(argv, cwd, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(argv, cwd=cwd, capture_output=True, encoding='utf-8', errors='replace', timeout=120)
    log.write_text(p.stdout+p.stderr, encoding='utf-8')
    if p.returncode:
        raise Failure('COMMAND_FAILED', f'{argv[0]} failed; see {log.name}')
    return p.stdout.strip()

def snapshot(repo, revision, dest, logs, subdir=None, project_compat=None):
    sha = command(['git','rev-parse','--verify','--end-of-options',revision+'^{commit}'], repo, logs/(dest.name+'-resolve.log'))
    command(['git','clone','--local','--no-hardlinks','--no-checkout',repo.as_posix(),dest.as_posix()], repo, logs/(dest.name+'-clone.log'))
    if subdir:
        command(['git', 'sparse-checkout', 'set', '--cone', '--', subdir], dest, logs/(dest.name+'-sparse.log'))
    command(['git','checkout','--detach',sha], dest, logs/(dest.name+'-checkout.log'))
    project = dest / subdir if subdir else dest
    if project.resolve() != project or not project.is_dir():
        raise Failure('UNSUPPORTED_PROJECT', 'Project directory is missing or traverses a symlink')
    # Fail early instead of silently ignoring unsupported project layouts.
    names = {p.name for p in project.glob('*.c')}
    if project_compat:
        supported = (
            project_compat['layout'] == 'root-make'
            and {'main.c','helper.c'}.issubset(names)
            and (project/'Makefile').is_file()
        )
    else:
        supported = names == {'main.c','helper.c'} and (project/'config.h').is_file()
    if not supported:
        raise Failure('UNSUPPORTED_PROJECT', 'Project files do not match the selected compatibility profile')
    return sha, project

def full(project, folder):
    from buildchecker.fullcheck import full_check
    report = full_check(project, folder)
    if report.get('status') != 'SUCCEEDED':
        raise Failure('FULL_CHECK_FAILED', str(report.get('error', report.get('error_code'))))
    return report

def normalized(findings):
    return sorted((f['type'],f['target'],f['dependency']) for f in findings if f['target'] in ('main.o','helper.o'))

class DraftRuntime:
    """Run project commands in the exact candidate image built for this job."""

    def __init__(self, image_id, logs):
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', image_id):
            raise Failure('DRAFT_FAILED', 'Candidate image ID is invalid')
        self.image_id = image_id
        self.host_root = os.environ['COURSE_HOST_ROOT']
        self.logs = logs
        self.sequence = 0

    def run(self, argv, project):
        self.sequence += 1
        prefix = self.logs / f'{self.sequence:03d}'
        source = Path(self.host_root) / project.resolve().relative_to(ROOT)
        invocation = [
            'docker', 'run', '--rm', '--pull', 'never', '--network', 'none',
            '--user', f'{os.getuid()}:{os.getgid()}',
            '--mount', f'type=bind,source={source},target=/project',
            '--workdir', '/project', '--entrypoint', argv[0], self.image_id, *argv[1:],
        ]
        record = {'image_id': self.image_id, 'project': str(project), 'command': invocation}
        try:
            result = command(invocation, project, prefix.with_suffix('.log'))
        except (Failure, OSError, subprocess.TimeoutExpired):
            save(prefix.with_suffix('.json'), dict(record, status='FAILED'))
            raise
        save(prefix.with_suffix('.json'), dict(record, status='SUCCEEDED'))
        return result

    def scan(self, project, old=None, *, real=False):
        flags = None
        if real:
            flags = shlex.split(self.run([
                'make', '-s', '--eval=__e12_flags: ; @printf "%s\\n" "$(CFLAGS)"', '__e12_flags',
            ], project))
        return scan(project, old, compiler_run=self.run, compiler_flags=flags)


def validate_in_draft(target, patchfile, edits, out, runtime, expected, project_profile):
    sandbox = out / 'sandbox'
    shutil.copytree(target, sandbox, ignore=shutil.ignore_patterns('.git', '*.o', 'app'))
    checks = {}
    edge_rebuilds = []
    make_profile = bool(project_profile)
    make_test = project_profile.get('make_test', False) if isinstance(project_profile, dict) else make_profile
    try:
        command(['git', 'init', '-b', 'main'], sandbox, out/'git-init.log')
        command(['git', 'add', '.'], sandbox, out/'git-add.log')
        command(['git', '-c', 'user.name=E12', '-c', 'user.email=e12@example.invalid',
                 'commit', '-m', 'E12 validation input'], sandbox, out/'git-commit.log')
        command(['git', 'apply', '--check', str(patchfile)], sandbox, out/'apply-check.log')
        command(['git', 'apply', str(patchfile)], sandbox, out/'apply.log')
        checks['patch_applies'] = True
        runtime.run(['make', 'clean'], sandbox)
        runtime.run(['make', 'app'], sandbox)
        checks['build'] = True
        if make_test:
            runtime.run(['make', 'test'], sandbox)
        checks['test'] = runtime.run(['./app'], sandbox) == expected
        edges = sorted({(edit['target'], edit['dependency']) for edit in edits})
        for target_name, dependency_name in edges:
            dependency = sandbox / dependency_name
            target_object = sandbox / target_name
            if not dependency.is_file() or not target_object.is_file():
                raise Failure(
                    'RECHECK_FAILED',
                    f'Missing dependency or target: {target_name} <- {dependency_name}',
                )
            before = target_object.stat().st_mtime_ns
            time.sleep(1.05)
            dependency.touch()
            runtime.run(['make', 'app'], sandbox)
            output = runtime.run(['./app'], sandbox)
            after = target_object.stat().st_mtime_ns
            rebuilt = after > before
            output_matches = output == expected
            edge_rebuilds.append({
                'target': target_name,
                'dependency': dependency_name,
                'before_mtime_ns': before,
                'after_mtime_ns': after,
                'rebuilt': rebuilt,
                'output': output,
                'output_matches': output_matches,
                'passed': rebuilt and output_matches,
            })
            save(out/'edge-rebuilds.json', edge_rebuilds)
        checks['edge_rebuilds'] = len(edge_rebuilds) == len(edges) and all(
            row['passed'] for row in edge_rebuilds
        )
        checks['header_change'] = checks['edge_rebuilds']
        recheck = runtime.scan(sandbox, real=make_profile)
        save(out/'recheck.json', recheck)
        checks['no_missing'] = not any(f['type'] == 'MISSING' for f in recheck['findings'])
    except (Failure, OSError, ValueError, subprocess.TimeoutExpired) as error:
        save(out/'validation.json', {'accepted': False, 'checks': checks, 'error': str(error),
                                     'rollback': True, 'source_unchanged': True, 'image_id': runtime.image_id})
        raise
    verdict = {'accepted': all(checks.values()), 'checks': checks, 'error': None,
               'rollback': not all(checks.values()), 'source_unchanged': True, 'image_id': runtime.image_id}
    save(out/'validation.json', verdict)
    return verdict, sandbox

def execute(request, out, job_id=None):
    job_id = job_id or 'job-'+uuid.uuid4().hex
    trace_id = 'trace-'+uuid.uuid4().hex
    if out.exists() and any(out.iterdir()):
        raise Failure('OUTPUT_EXISTS', 'Use a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    result = {'schema_version':'e11e12-1','job_id':job_id,'trace_id':trace_id,'status':'RUNNING','stages':[]}
    save(out/'request.json',request)
    def stage(name, commit, payload, files=()):
        envelope = {'schema_version':'e11e12-1','job_id':job_id,'trace_id':trace_id,'kind':name,
                    'commit':commit,'status':'SUCCEEDED','data':payload,
                    'artifacts':[artifact(p,out,job_id) for p in files]}
        save(out/(name+'.json'),envelope)
        result['stages'].append({'name':name,'artifact':artifact(out/(name+'.json'),out,job_id)})
        return envelope
    try:
        mode=request['mode']
        if mode not in ('e11-a','e11-b','e12'):
            raise Failure('INVALID_REQUEST','Unknown mode')
        project_compat=parse_project_compat(request,mode)
        offline_build=parse_offline_build(request,mode)
        repo=Path(request['repo']).resolve()
        if not repo.is_dir():
            raise Failure('INVALID_REQUEST','Repository missing')
        subdir = request.get('project_subdir')
        if subdir is not None and (
            not isinstance(subdir, str) or not subdir or '\\' in subdir
            or any(part in ('', '.', '..', '.git') for part in subdir.split('/'))
        ):
            raise Failure('INVALID_REQUEST', 'project_subdir must be a relative project path')
        if subdir and mode != 'e12':
            raise Failure('INVALID_REQUEST', 'project_subdir requires mode=e12')
        base_sha,base=snapshot(repo,request['base'],out/'base-project',out/'logs',subdir,project_compat)
        target_sha,target=snapshot(repo,request['target'],out/'target-project',out/'logs',subdir,project_compat)
        result.update(base_commit=base_sha,target_commit=target_sha)
        fixed_envelope = None
        if mode == 'e11-b':
            fixed_envelope=load_fixed_report(request)
            check_envelope(fixed_envelope,target_sha,'fixed-md')
            current=fixed_envelope['data']
            if current.get('commit') != target_sha:
                raise Failure('STALE_REPORT','Fixed report data commit mismatch')
            if project_compat:
                check_source_report(fixed_envelope,request['expected_source_report'])
            save(out/'fixed-md-input.json',fixed_envelope)
        runtime = None
        expected = request.get('expected_output','1')
        if mode in ('e11-b','e12'):
            from draft.autobuild import auto_build
            candidate=Path(request['candidate']).resolve()
            draft_kwargs = {'timeout': request.get('build_timeout', 600)}
            if offline_build is not None:
                draft_kwargs['offline'] = offline_build
            draft=auto_build(target,candidate,out/'draft-build',expected,**draft_kwargs)
            if draft['status']!='SUCCEEDED':
                raise Failure('DRAFT_FAILED',draft.get('error','Inspect draft-build logs'))
            stage('draft',target_sha,draft,[out/'draft-build/result.json'])
            if mode == 'e12' or project_compat:
                image_id = draft['attempts'][-1]['image_id']
                if 'COURSE_HOST_ROOT' not in os.environ:
                    raise Failure('DRAFT_RUNTIME_UNAVAILABLE', 'Start E12 through run_e11e12.py')
                runtime = DraftRuntime(image_id, out/'image-execution')
                result['image_id'] = image_id
        if mode in ('e11-a','e12'):
            base_full=full(base,out/'baseline-full')
            old=runtime.scan(base, real=bool(subdir)) if runtime else scan(base)
            edges=json.loads((out/'baseline-full/actual-graph.json').read_text())
            projected={t:sorted({e['dependency'] for e in edges if e['target']==t}) for t in ('main.o','helper.o')}
            if projected != old['actual']:
                raise Failure('GRAPH_MISMATCH','BuildChecker baseline differs from GCC observations')
            old['actual']=projected
            save(out/'baseline-cache.json',old)
            if runtime:
                base_full = dict(base_full, gcc_image_id=runtime.image_id)
            baseline=stage('full-check',base_sha,base_full,[out/'baseline-full/actual-graph.json',out/'baseline-full/findings.json',out/'baseline-cache.json'])
            check_envelope(baseline,base_sha,'full-check')
            current=runtime.scan(target,old,real=bool(subdir)) if runtime else scan(target,old)
            if runtime:
                current['image_id'] = runtime.image_id
            save(out/'incremental-report.json',current)
            reference=full(target,out/'target-full')
            if normalized(reference['findings']) != normalized(current['findings']):
                raise Failure('FINDINGS_MISMATCH','Incremental/full object-target findings differ')
            md_envelope=stage('incremental-check',target_sha,current,[out/'incremental-report.json',out/'target-full/findings.json'])
        else:
            # E11-B still consumes a fixed MD input, separately from A's live output.
            md_envelope=stage('fixed-md',target_sha,current,[out/'fixed-md-input.json'])
        if mode in ('e11-b','e12'):
            reference=result['stages'][-1]['artifact']
            report_path = out / (md_envelope['kind'] + '.json')
            before=(target/'Makefile').read_bytes()
            patchfile=out/'candidate.patch'
            kind = md_envelope['kind']
            edits = repair_from_artifact(target, report_path, reference['sha256'], kind, patchfile)
            save(out/'repair-plan.json',edits)
            stage('repair',target_sha,{'edits':edits,'input_report':reference},[patchfile,out/'repair-plan.json'])
            if runtime:
                profile = project_compat or ({'layout':'subdir-make','make_test':True} if subdir else False)
                verdict, sandbox = validate_in_draft(target, patchfile, edits, out/'validation', runtime, expected, profile)
            else:
                verdict = validate(target, patchfile, out/'validation')
                sandbox = target
            if not verdict['accepted']:
                raise Failure('REPAIR_REJECTED',str(verdict))
            try:
                final=full(sandbox,out/'final-full')
                if any(f['type']=='MISSING' for f in final['findings']):
                    raise Failure('RECHECK_FAILED','MD remains after repair')
            except (Failure, ValueError, OSError, subprocess.TimeoutExpired) as error:
                if not runtime:
                    (target/'Makefile').write_bytes(before)
                verdict.update(accepted=False, rollback=True, source_unchanged=True, error=str(error))
                save(out/'validation/validation.json',verdict)
                raise
            if runtime:
                (target/'Makefile').write_bytes((sandbox/'Makefile').read_bytes())
                verdict['source_unchanged'] = False
                save(out/'validation/validation.json', verdict)
            recheck_payload={'validation':verdict,'findings':final['findings'],'patched_makefile_sha256':hashlib.sha256((target/'Makefile').read_bytes()).hexdigest()}
            recheck_files=[out/'validation/validation.json',out/'final-full/findings.json']
            if (out/'validation/recheck.json').is_file():
                recheck_payload['gcc_findings']=json.loads((out/'validation/recheck.json').read_text(encoding='utf-8')).get('findings',[])
                recheck_files.append(out/'validation/recheck.json')
            if (out/'validation/edge-rebuilds.json').is_file():
                recheck_files.append(out/'validation/edge-rebuilds.json')
            stage('recheck',target_sha,recheck_payload,recheck_files)
        result['status']='SUCCEEDED'
    except (Failure,ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        result.update(status='TIMED_OUT' if isinstance(exc,subprocess.TimeoutExpired) else 'FAILED',error={'code':getattr(exc,'code','EXECUTION_FAILED'),'message':str(exc)})
    result['artifacts']=[artifact(p,out,job_id) for p in sorted(out.rglob('*')) if p.is_file() and '.git' not in p.parts and not p.is_symlink()]
    save(out/'result.json',result)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=execute(json.loads(a.request.read_text(encoding='utf-8')),a.out.resolve());print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['status']=='SUCCEEDED' else 1

if __name__=='__main__':raise SystemExit(main())
