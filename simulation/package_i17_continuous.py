"""Freeze exact C-to-A increment; never modify the native Vivado checkout.

Run: python simulation/package_i17_continuous.py
Output: deliverables/i17-continuous-control-20261013-<content-id>.zip + sha256.
Next: A integrates the seven RTL sources in the existing project per README.
"""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/evidence/issue19-continuous-control-20261013'
RUNS=ROOT/'codex_out/i17-continuous-control-20261013/runs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def package():
    rtl=json.loads((DOC/'candidate-files.json').read_text())['rtl']
    native=json.loads((ROOT/'codex_out/i17-continuous-control-20261013/preimages.json').read_text())
    (DOC/'patches').mkdir(exist_ok=True)
    for item in native:
        before=Path(item['native']);after=ROOT/item['target']
        if sha(before)!=item['preimage_sha256']:raise RuntimeError('native preimage changed: '+str(before))
        item['candidate_sha256']=sha(after)
        diff=''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),
            fromfile='native/'+before.name,tofile=item['target']))
        (DOC/'patches'/f'{before.name}.patch').write_text(diff,encoding='utf-8')
    write(DOC/'preimages.json',native)
    for item in json.loads((DOC/'reference-manifest.json').read_text()):
        if sha(DOC/item['path'])!=item['sha256']:raise RuntimeError('reference changed: '+item['path'])
    chosen=['control-7','export-1','watchdog-2','canary_export-1','full_probe-1','full_stop-5','full_stall-1']
    checks=[]
    for name in chosen:
        folder=RUNS/name
        if not (folder/'run.json').exists():continue
        record=json.loads((folder/'run.json').read_text())
        match=all(Path(p).is_file() and sha(Path(p))==h for p,h in record['sources'].items())
        summary={'run':name,'verdict':record.get('verdict','RUNNING'),'source_matches_current':match,
            'scope':record['scope'],'stages':record['stages']}
        checks.append(summary)
        if 'verdict' not in record:continue
        target=DOC/'originals'/name;target.mkdir(parents=True,exist_ok=True)
        for p in [folder/'run.json',*folder.glob('*.log'),*folder.glob('events.csv')]:
            if p.is_file():(target/p.name).write_bytes(p.read_bytes())
        # Retain the old frozen source for explicit mismatched/failed evidence.
        if not match:
            for p in (folder/'sources').glob('*'):
                if p.suffix in ('.sv','.v'):
                    q=target/'sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
    complete=next(x for x in checks if x['run']=='full_stop-5')
    full_ok=complete['verdict']=='FUNCTIONAL_SIM_PASS' and complete['source_matches_current']
    write(DOC/'validation.json',{'status':'RTL_CONTINUOUS_STOP_PASS' if full_ok else 'CONTROL_UNIT_PASS_FULL_CHAIN_UNVERIFIED',
        'checks':checks,'default_warmup':'UNVERIFIED','physical_resources_sta_cdc':'NOT_RUN',
        'board_follow_stop_restart':'NOT_RUN','pynq':'UNVERIFIED','a_integrated':'UNVERIFIED'})
    inputs={p:sha(ROOT/p) for p in rtl}
    identifier=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    write(DOC/'candidate-manifest.json',{'rtl_content_id':identifier,'rtl':inputs,
        'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'part':'xc7z020clg400-1','tool':'Vivado 2025.2','clock_hz':61440000,
        'native_project_written':False,'physical_build_run':False})
    assets=[ROOT/p for p in rtl]+[ROOT/'simulation/run_i17_continuous.py',Path(__file__).resolve(),
        *sorted((ROOT/'simulation/tb/c_board').glob('tb_i17_*.sv')),*sorted(p for p in DOC.rglob('*') if p.is_file())]
    manifest={p.relative_to(ROOT).as_posix():sha(p) for p in assets}
    if len(manifest)!=len(assets):raise RuntimeError('duplicate package path')
    payload_id=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:8]
    output=ROOT/'deliverables'/f'i17-continuous-control-20261013-{identifier[:12]}-{payload_id}.zip'
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in assets:archive.write(p,p.relative_to(ROOT).as_posix())
        archive.writestr('SHA256SUMS.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(output) as archive:
        for name,h in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=h:raise RuntimeError('ZIP mismatch: '+name)
    output.with_suffix('.sha256').write_text(sha(output)+'  '+output.name+'\n',encoding='ascii')
    print(json.dumps({'path':str(output),'sha256':sha(output),'entries':len(manifest),
        'rtl_content_id':identifier,'status':json.loads((DOC/'validation.json').read_text())['status']},indent=2))

if __name__=='__main__':package()
