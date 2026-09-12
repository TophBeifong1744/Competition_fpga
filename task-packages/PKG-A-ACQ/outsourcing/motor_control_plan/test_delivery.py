"""Negative controls for check_delivery.py, in temporary copies only.
Run: python test_delivery.py --root . ; stdout results, nonzero on any failure.
Requires an up-to-date manifest; next repeat checker on fetched commit bytes.
"""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);a=ap.parse_args()
    source=a.root.resolve();records=[]
    with tempfile.TemporaryDirectory(prefix='motor_delivery_check_') as tmp:
        root=Path(tmp)/'package'
        shutil.copytree(source,root,ignore=shutil.ignore_patterns('__pycache__','results-reproduced-*'))
        manifest=json.loads((root/'manifest.json').read_text());base=json.dumps(manifest,indent=2).encode()
        def invoke(label,expected):
            p=subprocess.run([sys.executable,str(source/'check_delivery.py'),'--root',str(root)],capture_output=True,text=True)
            if (p.returncode==0)!=expected:raise AssertionError(label+': '+p.stdout+p.stderr)
            records.append({'name':label,'expected_success':expected,'exit_code':p.returncode})
        def replace(name,data,rehash=False):
            p=root/name;original=p.read_bytes();p.write_bytes(data)
            if rehash:
                m=json.loads(base);m['files'][name]=hashlib.sha256(data).hexdigest()
                (root/'manifest.json').write_text(json.dumps(m),encoding='utf-8')
            return original
        def restore(name,data):
            (root/name).write_bytes(data);(root/'manifest.json').write_bytes(base)
        invoke('intact_copy',True)
        name='results/run.log';original=(root/name).read_bytes();(root/name).unlink()
        invoke('missing_log',False);restore(name,original)
        name='README.md';original=replace(name,(root/name).read_bytes()+b'X')
        invoke('hash_mismatch',False);restore(name,original)
        name='results/motion.png';original=replace(name,b'bad png',True)
        invoke('bad_png_even_with_matching_hash',False);restore(name,original)
        name='results/traces.npz';original=replace(name,(root/name).read_bytes()[:100],True)
        invoke('truncated_npz_even_with_matching_hash',False);restore(name,original)
        import io
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('array.npy',b'not an NPY array')
        name='results/full_range.npz';original=replace(name,buf.getvalue(),True)
        invoke('valid_zip_invalid_array_even_with_matching_hash',False);restore(name,original)
        invoke('restored_copy',True)
    print(json.dumps({'checks':records,'pass_count':len(records)},indent=2))
if __name__=='__main__':main()
