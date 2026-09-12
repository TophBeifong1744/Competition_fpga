"""Prepare/verify a pinned mixed-status stage index, never an acceptance decision."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE='add40fd773eccdad80f26624ca899c331d6846c8'
DEST=ROOT/'deliverables/phase-2026-09-16/manifest.json'
GROUPS={
 'phase_rules':('planning_and_current_status',['docs/phases/2026-09-11-to-09-16','docs/team-workflow.md','docs/phase-closeout.md','docs/current-status.md']),
 'b_four_receipt':('limited_reviewed_diagnostic',['task-packages/PKG-B-ALG/tasks/four-channel-receipt-01','task-packages/PKG-B-ALG/payload/model/python/h1_reader.py']),
 'a_real_recording':('B_received_diagnostic_not_formal_H2',['task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911']),
 'a_engineering':('limited_engineering_material_and_software_review',['task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01']),
 'a_fft29':('limited_60_frame_forward_core_and_OOC_review',['task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01']),
 'b_fixed_research':('mixed_limited_review_and_user_authorized_archive_not_full_A_approval',['task-packages/PKG-B-ALG/tasks/fft-bitexact-01','task-packages/PKG-B-ALG/tasks/fft-window-02','task-packages/PKG-B-ALG/tasks/phat-fixed-03']),
 'b_review_scope':('exact_approval_and_authorization_records',['docs/reviews/fixed-closeout-6cb76d1','docs/reviews/b-fixed-user-20260912']),
 'c004_status':('pending_formal_approval_R2_deferred_005_not_started',['task-packages/PKG-A-ACQ/outsourcing/review-status/c004-next-stage-20260911.md'])}

def git(*args,input=None):
    return subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT,input=input)

def blob_values(oids):
    # One batch avoids one Git process per evidence file. No shell interpolation.
    data=io.BytesIO(git('cat-file','--batch',input=('\n'.join(oids)+'\n').encode()))
    for oid in oids:
        header=data.readline().decode().strip().split()
        assert len(header)==3 and header[0]==oid and header[1]=='blob',header
        value=data.read(int(header[2]));assert data.read(1)==b'\n'
        yield value

def construct(export=None):
    assert git('rev-parse',BASE).decode().strip()==BASE
    tree={}
    for entry in git('ls-tree','-r','-z',BASE).split(b'\0'):
        if not entry:continue
        meta,name=entry.split(b'\t',1);mode,kind,oid=meta.decode().split()
        if kind=='blob':tree[name.decode()]={'mode':mode,'blob':oid}
    chosen={}
    for group,(status,paths) in GROUPS.items():
        for prefix in paths:
            matches=[name for name in tree if name==prefix or name.startswith(prefix+'/')]
            assert matches,('missing source',prefix)
            for name in matches:chosen.setdefault(name,[]).append(group)
    names=sorted(chosen);rows=[]
    for name,value in zip(names,blob_values([tree[n]['blob'] for n in names]),strict=True):
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        row=dict(path=name,groups=sorted(set(chosen[name])),git_blob=tree[name]['blob'],bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
        rows.append(row)
        if export:
            target=export/name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as handle:handle.write(value)
            assert hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256']
    old={}
    prefix='deliverables/phase-2026-09-10/'
    assert not git('diff','--exit-code',BASE,'--',prefix),'Previous tracked archive changed'
    for name,value in zip(sorted(n for n in tree if n.startswith(prefix)),blob_values([tree[n]['blob'] for n in sorted(n for n in tree if n.startswith(prefix))]),strict=True):
        # Git text checkout conversion is not an edit. Check original ZIP bytes separately.
        expected=hashlib.sha256(value).hexdigest()
        if name.endswith('.zip'):
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,('old archive changed',name)
        old[name]=expected
    return dict(status='PENDING_GROUP_LEADER_CONFIRMATION_NOT_ACCEPTED',prepared_date='2026-09-12',planned_check_date='2026-09-16',
        source_commit=BASE,group_status={k:v[0] for k,v in GROUPS.items()},
        file_count=len(rows),total_bytes=sum(r['bytes'] for r in rows),files=rows,protected_previous_archive=old)

def main():
    ap=argparse.ArgumentParser();m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument('--build',action='store_true');m.add_argument('--verify',action='store_true')
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--export',type=Path)
    args=ap.parse_args()
    if args.out.exists() or (args.export and args.export.exists()):raise ValueError('New output/export directories required')
    if args.export:
        if args.export.resolve()==args.out.resolve():raise ValueError('Separate output and export directories required')
        args.export.mkdir(parents=True)
    args.out.mkdir(parents=True)
    actual=construct(args.export)
    if args.build:
        with DEST.open('x',encoding='utf-8') as handle:json.dump(actual,handle,indent=2,ensure_ascii=False);handle.write('\n')
    else:assert json.loads(DEST.read_text(encoding='utf-8'))==actual,'Index differs from fixed source'
    result=dict(status='PASS_PINNED_INDEX_NOT_STAGE_ACCEPTANCE',source_commit=BASE,file_count=actual['file_count'],
        total_bytes=actual['total_bytes'],group_counts={k:sum(k in r['groups'] for r in actual['files']) for k in GROUPS},
        prior_archive_files_unchanged=len(actual['protected_previous_archive']),
        prior_archive_check='Git tracked diff against pinned source plus binary ZIP byte hashes; text checkout conversion is not byte identity',
        manifest_sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        python=sys.version,command=sys.argv,exported=bool(args.export))
    (args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
