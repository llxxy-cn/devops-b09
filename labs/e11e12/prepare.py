import json
from pathlib import Path
from pipeline import ROOT, save
from lab import fixture,commit,scan

DRAFT_BASE_TAG='python:3.13-slim'
DRAFT_BASE_PIN=DRAFT_BASE_TAG+'@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74'
DRAFT_APT_MIRROR_RUN=(
    "RUN sed -i "
    "-e 's|https\\?://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' "
    "-e 's|https\\?://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' "
    "-e 's|https\\?://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' "
    "/etc/apt/sources.list.d/debian.sources"
)

def main():
    root=ROOT/'data/integration-sample'
    if root.exists():raise SystemExit('data/integration-sample already exists; preserve it and choose a new workspace')
    project=root/'repo';fixture(project)
    broken=f'FROM {DRAFT_BASE_TAG}\nWORKDIR /work\nCOPY main.c helper.c config.h extra.h unused.h Makefile ./\nRUN make app\nCMD ["./app"]\n'
    (project/'Dockerfile.broken').write_text(broken,encoding='utf-8')
    base=commit(project,'integration C0')
    (project/'main.c').write_text('#include "extra.h"\n'+(project/'main.c').read_text(),encoding='utf-8')
    target=commit(project,'integration C1 add project include')
    pin=f'FROM {DRAFT_BASE_PIN}'
    candidate=broken.replace(f'FROM {DRAFT_BASE_TAG}',pin).replace('RUN make app','RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*\nRUN make app')
    candidate=candidate.replace('RUN apt-get update',DRAFT_APT_MIRROR_RUN+'\nRUN apt-get update')
    (root/'candidate.Dockerfile').write_text(candidate,encoding='utf-8')
    fixed=scan(project)
    save(root/'fixed-md.json',{'schema_version':'e11e12-1','kind':'fixed-md','status':'SUCCEEDED','commit':target,'data':fixed})
    for mode in ('e11-a','e11-b','e12'):
        save(root/(mode+'.json'),{'mode':mode,'repo':str(project),'base':base,'target':target,'candidate':str(root/'candidate.Dockerfile'),'fixed_report':str(root/'fixed-md.json'),'expected_output':'1','build_timeout':600})
    save(root/'dataset.json',{'source':'course-generated controlled C/Make project','base_commit':base,'target_commit':target,'candidate_source':'recorded dependency-install pattern adapted to the two-source-file project','expected_output':'1','purpose':'classroom baseline; replace request paths with your own project for real-data integration'})
    print(root)

if __name__=='__main__':main()
