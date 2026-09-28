"""Read-only diagnosis: never normalizes or patches a live checker."""
import argparse, ast, difflib, hashlib, json, subprocess, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    base='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/'
    scene=base+'batches/background-target-stop-20260917/'
    continuous=base+'continuous-prototype-01/'
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    policy=json.loads((root/scene/'POLICY.json').read_text())
    sha=lambda b:hashlib.sha256(b).hexdigest()
    rows=[]
    for rel,expected in policy['checker_dependencies'].items():
        path=continuous+rel
        actual=(root/path).read_bytes()
        blob=subprocess.check_output(['git','show',head+':'+path])
        rows.append(dict(path=path,expected=expected,actual=sha(actual),git=sha(blob),
                         lf=sha(actual.replace(b'\r\n',b'\n')),
                         actual_matches=sha(actual)==expected,git_matches=sha(blob)==expected,
                         working_equals_git=actual==blob,
                         normalized_working_equals_git=actual.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')))
    rel=continuous+'timerfixed-entry-01/'
    old=(root/rel/'repair-01/originals/check_entry.py').read_bytes()
    new=(root/rel/'check_entry.py').read_bytes()
    pin='21c141b223936730c2ce5139624fcedb412adafb'
    approved=subprocess.check_output(['git','show',pin+':'+rel+'check_entry.py'])
    assert sha(old)==policy['checker_dependencies']['timerfixed-entry-01/check_entry.py']
    assert new==approved
    (out/'old-vs-approved.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='S1-pinned-original',tofile=pin)),encoding='utf-8')
    def functions(data):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(data).body if isinstance(n,ast.FunctionDef)}
    before,after=functions(old),functions(new)
    delta=dict(old_sha256=sha(old),approved_commit=pin,new_sha256=sha(new),
               changed_functions=[n for n in sorted(before.keys()|after.keys()) if before.get(n)!=after.get(n)])
    files=['build/four_mic_endurance.elf','build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',
           '_ide/launch.json','_ide/bitstream/system_continuous_20260915.bit','_ide/psinit/ps7_init.tcl']
    app=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
    artifacts={str(app/f):sha((app/f).read_bytes()) for f in files}
    report=dict(head=head,argv=sys.argv,python=sys.version,dependencies=rows,checker_change=delta,artifacts=artifacts,
                changes_to_actual_files=False,load_check='NOT_PASSED',board='NOT_RUN')
    (out/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
