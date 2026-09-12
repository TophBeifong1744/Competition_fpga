"""Check exact delivery bytes and decode all binary evidence. Python + NumPy + Pillow.
Run: python check_delivery.py --root .
Maintainer: stage package, then --write-manifest-from-index; stage manifest afterward.
Outputs: stdout PASS/FAIL, optional JSON via --report (place outside the package).
Next: repeat on a clean extraction of the exact fetched remote commit.
"""
import argparse,hashlib,io,json,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
import numpy as np
from PIL import Image

REQUIRED={'README.md','motor_plan.md','report.html','simulate.py','validate_control.py',
          'run_all.ps1','check_delivery.py','test_delivery.py','rework_notes.md',
          '.gitattributes','.gitignore','results/run.log','results/control_run.log',
          'results/rework_checks.log','results/verification.json','results/control_checks.json',
          'results/restoration.json','results/motion.png','results/robustness.png',
          'results/traces.npz','results/full_range.npz','results/reversal.npz',
          'results/controlled_stop.npz','results/negative_control.npz'}

def decode(name,data):
    if name.lower().endswith('.png'):
        with Image.open(io.BytesIO(data)) as im:
            if im.format!='PNG':raise ValueError('not PNG')
            im.verify()
        with Image.open(io.BytesIO(data)) as im:im.load()
        return {'png':1,'npz':0,'arrays':0}
    if name.lower().endswith('.npz'):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if z.testzip() is not None:raise ValueError('ZIP CRC failure')
            if not z.namelist() or len(set(z.namelist()))!=len(z.namelist()):raise ValueError('empty/duplicate members')
            if any(not n.endswith('.npy') for n in z.namelist()):raise ValueError('unexpected NPZ member')
        with np.load(io.BytesIO(data),allow_pickle=False) as a:
            if not a.files:raise ValueError('no arrays')
            for key in a.files:
                arr=a[key] # Force every array to be loaded, not just ZIP headers.
                if arr.dtype.hasobject:raise ValueError('object array')
                if np.issubdtype(arr.dtype,np.number) and not np.isfinite(arr).all():raise ValueError('non-finite array')
            count=len(a.files)
        return {'png':0,'npz':1,'arrays':count}
    return {'png':0,'npz':0,'arrays':0}

def safe_name(name):
    p=PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name

def payload_files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and '.git' not in p.parts
            and not any(x.startswith('results-reproduced-') for x in p.relative_to(root).parts)
            and p.name!='manifest.json' and p.suffix not in {'.pyc','.pyo'}}

def validate(root,manifest=None):
    errors=[];counts={'files':0,'png':0,'npz':0,'arrays':0}
    try:
        manifest=manifest or json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('schema')!='motor_delivery_manifest_v2':raise ValueError('unsupported manifest schema')
        entries=manifest['files']
        if not REQUIRED<=set(entries):errors.append('required entries missing: '+str(sorted(REQUIRED-set(entries))))
        extra=payload_files(root)-set(entries)
        if extra:errors.append('unlisted files: '+str(sorted(extra)))
        for name,expected in entries.items():
            if not safe_name(name):errors.append('unsafe path: '+name);continue
            p=root/name
            if not p.is_file():errors.append('missing: '+name);continue
            if p.is_symlink():errors.append('symlink not allowed: '+name);continue
            data=p.read_bytes();counts['files']+=1
            if hashlib.sha256(data).hexdigest()!=expected:errors.append('hash: '+name)
            try:
                c=decode(name,data)
                for k,v in c.items():counts[k]+=v
            except Exception as e:errors.append(f'decode: {name}: {type(e).__name__}: {e}')
    except Exception as e:errors.append(f'manifest: {type(e).__name__}: {e}')
    return {'pass':not errors,'counts':counts,'errors':errors}

def index_manifest(root):
    def git(*args):
        return subprocess.check_output(['git','-c',f'safe.directory={repo}', '-C',str(repo),*args])
    # Discover the repo without changing any global trust/config setting.
    repo=next((p for p in [root,*root.parents] if (p/'.git').exists()),None)
    if repo is None:raise ValueError('manifest creation requires Git index')
    prefix=root.relative_to(repo).as_posix()+'/'
    entries={}
    for row in git('ls-files','--stage','-z','--',prefix).split(b'\0'):
        if not row:continue
        meta,path=row.split(b'\t',1);mode,oid,stage=meta.decode().split()
        if stage!='0':raise ValueError('unmerged index')
        if mode!='100644' and mode!='100755':raise ValueError('non-regular file')
        name=path.decode('utf-8')[len(prefix):]
        if name=='manifest.json':continue
        data=git('cat-file','blob',oid)
        if data!=(root/name).read_bytes():raise ValueError(f'index/worktree byte mismatch: {name}; normalize text to LF and restage')
        decode(name,data) # Never generate hashes that bless undecodable binaries.
        entries[name]=hashlib.sha256(data).hexdigest()
    result={'schema':'motor_delivery_manifest_v2',
            'hash_basis':'SHA-256 of actual staged Git blob bytes; verified identical to working tree. manifest.json excludes itself.',
            'files':dict(sorted(entries.items()))}
    checked=validate(root,result)
    if not checked['pass']:raise ValueError(json.dumps(checked))
    (root/'manifest.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    return checked

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--write-manifest-from-index',action='store_true');ap.add_argument('--report',type=Path)
    a=ap.parse_args()
    try:result=index_manifest(a.root.resolve()) if a.write_manifest_from_index else validate(a.root.resolve())
    except Exception as e:result={'pass':False,'errors':[f'{type(e).__name__}: {e}']}
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
