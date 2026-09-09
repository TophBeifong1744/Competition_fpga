"""Check completed A results and seal copied evidence; never alters originals."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);read=lambda p:json.loads(p.read_text(encoding='utf-8'))
assert read(root/'integration-r3/result.json')['status']=='PASS'
assert read(root/'review-r3-intel01/run.json')['status']=='PASS'
assert read(root/'stable-independent-r3.json')['status']=='PASS_EXACT_INPUT_AND_NUMERIC_REPRODUCTION'
files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p.name!='files.json'}
out=root/'files.json';assert not out.exists()
out.write_text(json.dumps(dict(reviewed_sha='6491d1bab04038b71fdd8c22d45a58455aa58ade',files=files),indent=2)+'\n',encoding='utf-8')
print('PASS; sealed A evidence files:',len(files))
