"""Build a bounded, portable diagnostic package, including ignored raw evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a = p.parse_args()
repo = a.repo.resolve()
task = repo/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01'
review = Path(__file__).resolve().parent
b = repo/'task-packages/PKG-B-ALG'
out = a.output.resolve()
archive = out.with_suffix('.zip')
if out.exists() or archive.exists():
    raise FileExistsError('Choose a fresh package/output name; preserve earlier evidence')
out.mkdir(parents=True)
for name in ('dupont-quiet-01','dupont-speech-01','listening-01'):
    shutil.copytree(task/'captures'/name,out/'captures'/name)
shutil.copy2(task/'captures/dupont-reader-check-01.log',out/'captures/dupont-reader-check-01.log')
for name in ('run01','run02','build-snapshot'):
    shutil.copytree(review/name,out/name)
for name in ('REVIEW.md','B-HANDOFF.md','audit_capture.py','audit_listening.py',
             'snapshot_build.py','verify_manifest.py','make_handoff.py'):
    shutil.copy2(review/name,out/name)
for name in ('export_four.py','export_c_capture.py','test_export.py','test_c_capture_gate.py'):
    (out/'source').mkdir(exist_ok=True)
    shutil.copy2(task/'source'/name,out/'source'/name)
for name in ('payload/model/python/h1_reader.py','payload/tb/python/test_h1_reader.py',
             'payload/docs/h1-reader.md'):
    (out/'b-reader'/name).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(b/name,out/'b-reader'/name)
fixture = Path('reference/h1-ss-data-draft-0.3/payload/examples/h1')
shutil.copytree(b/fixture,out/'b-reader'/fixture)
# Freeze exactly the inputs whose hashes were reviewed, not newer files with the same names.
integrity = json.loads((out/'run02/integrity.json').read_text())
for segment in integrity['segments']:
    for name,expected in segment['raw_file_sha256'].items():
        assert sha(out/'captures'/segment['acquisition_id']/name) == expected
assert sha(out/'b-reader/payload/model/python/h1_reader.py') == integrity['reader_sha256']
assert sha(out/'audit_capture.py') == integrity['review_script_sha256']
assert sha(out/'captures/dupont-reader-check-01.log') == integrity['submitted_reader_log_sha256']
listening = json.loads((out/'run02/listening.json').read_text())
assert sha(out/'captures/listening-01/listening-info.json') == listening['info_sha256']
for entry in listening['files']:
    assert sha(out/'captures/listening-01'/entry['file']) == entry['sha256']
for name,entry in json.loads((out/'build-snapshot/manifest.json').read_text()).items():
    assert sha(out/'build-snapshot'/name) == entry['sha256']
files = sorted(path for path in out.rglob('*') if path.is_file())
manifest = {path.relative_to(out).as_posix():sha(path) for path in files}
(out/'MANIFEST.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(path for path in out.rglob('*') if path.is_file()):
        z.write(path,Path(out.name)/path.relative_to(out))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,expected in manifest.items():
        assert hashlib.sha256(z.read(out.name+'/'+name)).hexdigest() == expected
print(json.dumps({'zip':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,
                  'payload_files':len(manifest),'zip_crc_and_all_hashes':'PASS'},indent=2))
