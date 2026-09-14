"""Check immutable evidence bytes; this is not technical approval."""
import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_bytes())
bad=[]
if hashlib.sha256((root/manifest['review_doc']).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=manifest['review_doc_sha256']:
 bad.append(manifest['review_doc'])
for item in manifest['files']:
 p=root/item['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
  bad.append(item['path'])
print(json.dumps(dict(files=len(manifest['files']),mismatches=bad,scope='byte integrity only'),indent=2))
sys.exit(bool(bad))
