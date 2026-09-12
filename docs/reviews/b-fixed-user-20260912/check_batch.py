"""Post-merge checks for explicitly authorized research archive integration."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
SCOPES=['task-packages/PKG-B-ALG/tasks/'+n for n in ['fft-bitexact-01','fft-window-02','phat-fixed-03']]
GIT=['git','-c',f'safe.directory={ROOT.as_posix()}','-C',str(ROOT)]
SOURCE='fdc2d18f2d765cad3223720a85680fd102185039'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    tree=subprocess.check_output(GIT+['ls-tree','-r','-z',SOURCE,'--',*SCOPES])
    tracked=[]
    for row in tree.split(b'\0'):
        if not row: continue
        meta,name=row.split(b'\t',1);path=name.decode();blob=meta.split()[2].decode()
        raw=(ROOT/path).read_bytes()
        assert hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()==blob,path
        tracked.append(path)
    sealed=[]
    for relative in ['fft-window-02/hashes.json','phat-fixed-03/integration/manifest.json','phat-fixed-03/dynamic-range/manifest.json']:
        p=ROOT/'task-packages/PKG-B-ALG/tasks'/relative
        for name,h in json.loads(p.read_text()).items():
            assert digest(p.parent/name)==h,name
        sealed.append(dict(manifest=str(p.relative_to(ROOT)),entries=len(json.loads(p.read_text()))))
    for commit in ['bff45e7bbedab321fc4815e1432f1575c750edc4',SOURCE]:
        subprocess.run(GIT+['merge-base','--is-ancestor',commit,'HEAD'],check=True)
    # A's PR11 clarification and evidence are untouched by these user archive merges.
    assert not subprocess.check_output(GIT+['diff','02a41b4507b4544e2fdf1d20a28996997110c337','HEAD','--','docs/reviews/fixed-closeout-6cb76d1'])
    logs=['task-packages/PKG-B-ALG/tasks/phat-fixed-03/dynamic-range/run01-console.log',
          'task-packages/PKG-B-ALG/tasks/phat-fixed-03/integration/evidence/run02-console.log']
    r=dict(status='USER_AUTHORIZED_ARCHIVE_INTEGRATION_CHECK_NOT_NEW_A_APPROVAL',
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),
        head=subprocess.check_output(GIT+['rev-parse','HEAD'],text=True).strip(),
        source=SOURCE,source_files_git_bytes_equal=len(tracked),sealed_manifests=sealed,
        recovered_original_logs={p:digest(ROOT/p) for p in logs},commands=[])
    task=ROOT/'task-packages/PKG-B-ALG/tasks'
    commands=[['closeout-manifest',task/'phat-fixed-03/closeout-01/verify_delivery.py'],
              ['window-archive',task/'fft-window-02/verify_archive.py','--out',out/'window-check.json'],
              ['phat-arithmetic',task/'phat-fixed-03/validate.py','--seed-offset','10000','--out',out/'phat'],
              ['closeout-analysis',task/'phat-fixed-03/closeout-01/analyze.py','--out',out/'analysis']]
    for label,*argv in commands:
        command=[sys.executable,'-B',*map(str,argv)]
        p=subprocess.run(command,cwd=ROOT,capture_output=True)
        (out/f'{label}.stdout.txt').write_bytes(p.stdout);(out/f'{label}.stderr.txt').write_bytes(p.stderr)
        r['commands'].append(dict(label=label,argv=command,cwd=str(ROOT),exit_code=p.returncode))
        (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
        assert p.returncode==0,label
    stable=['amplitude.csv','numerical-loss.csv','pairs.csv','research-lines.json','stage-amplitude.csv','stage-pairs.csv','strata.json','tail-cases.json']
    r['analysis_numeric_outputs_bytes_equal']={n:digest(out/'analysis'/n)==digest(task/'phat-fixed-03/closeout-01/evidence/run01'/n) for n in stable}
    assert all(r['analysis_numeric_outputs_bytes_equal'].values())
    (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(tracked)} original Git files, sealed manifests incl recovered logs, 4 post-merge checks')

if __name__=='__main__': main()
