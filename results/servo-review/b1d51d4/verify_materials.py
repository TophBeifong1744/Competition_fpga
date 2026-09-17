"""Batch-specific source identity, evidence and local-link audit."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
pin = 'b1d51d44aa2c055a145b832b7c272fd33b7d0395'
package = 'task-packages/PKG-SERVO-PWM'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)
candidate_paths = git('ls-tree','-r','--name-only',pin,package).decode().splitlines()
for relative in candidate_paths:
    expected = git('show',f'{pin}:{relative}')
    assert (root/relative).read_bytes().replace(b'\r\n',b'\n') == expected.replace(b'\r\n',b'\n'), relative
for kind, name in [('rtl','motor_drive.v'), ('tb','tb_motor_drive.v')]:
    assert (root/kind/'servo'/name).read_bytes() == (root/package/kind/name).read_bytes()
manifest = json.loads((root/'sim/modules.json').read_text())
for entry in manifest['files']:
    data = (root/entry['target']).read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(data).hexdigest() == entry['normalized_sha256'], entry['target']
changed = git('diff','--name-only').decode().splitlines()
new_docs = ['docs/reviews/servo-b1d51d4/REVIEW.md','docs/maintenance/servo-publication-2026-09-17.md',
            'hardware/servo-camera-decision.md']
link_count=0
for relative in changed+new_docs:
    file=root/relative
    if file.suffix!='.md': continue
    for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
        target=target.split('#')[0]
        if not target or '://' in target or target.startswith('mailto:'): continue
        assert (file.parent/target).resolve().exists(), (relative,target)
        link_count+=1
retained=[]
cache=[]
for file in sorted(evidence.rglob('*')):
    if not file.is_file(): continue
    rel=file.relative_to(evidence)
    if file.name in ('hashes.json','audit.json','cache-files.json','batch-paths.txt'): continue
    parts=rel.parts
    duplicate_fixture='task-packages' in parts
    keep=(file.suffix in ('.md','.py','.sv','.json','.txt','.log') or file.name=='.gitattributes')
    if duplicate_fixture:
        keep=file.name=='motor_drive.v'
    if 'xsim.dir' in parts or file.suffix in ('.jou','.pb','.wdb','.wcfg','.prj','.str','.xml'):
        keep=False
    (retained if keep else cache).append(file)
hashes={f.relative_to(evidence).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in retained}
(evidence/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
(evidence/'cache-files.json').write_text(json.dumps([str(f) for f in cache],indent=2),encoding='utf-8')
result=dict(candidate=pin,candidate_files=len(candidate_paths),activity_files=2,manifest_files=len(manifest['files']),
            local_links=link_count,evidence_files=len(retained),cache_files=len(cache),status='PASS')
(evidence/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
paths=changed+new_docs+candidate_paths+['rtl/servo/motor_drive.v','tb/servo/tb_motor_drive.v','sim/run_servo.ps1']
paths += [f.relative_to(root).as_posix() for f in retained]
paths += ['results/servo-review/b1d51d4/'+f for f in ('hashes.json','audit.json','cache-files.json')]
(evidence/'batch-paths.txt').write_text('\n'.join(sorted(set(paths)))+'\n',encoding='utf-8')
print(json.dumps(result))
