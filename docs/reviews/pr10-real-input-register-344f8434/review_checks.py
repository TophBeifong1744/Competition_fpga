"""A registration/provenance review only: no numerical/audio replay."""
import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

PIN = '344f8434c54187f7c5d412ee1ef38335a433beff'
MAIN = '4957d18837f79eca7a6acc86a2757d10f41dd410'
REL = 'task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911'
A_REL = 'task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    def run(argv, label=None, expected=0):
        r = subprocess.run(argv, cwd=repo, env=env, capture_output=True)
        commands.append(dict(argv=argv, cwd=str(repo), exit_code=r.returncode, expected=expected))
        if label:
            (out/(label+'.stdout.txt')).write_bytes(r.stdout)
            (out/(label+'.stderr.txt')).write_bytes(r.stderr)
        assert r.returncode == expected, (argv, r.stderr.decode('utf-8', errors='replace'))
        return r.stdout
    def git(*args):
        return run(['git', '-c', 'safe.directory='+repo.as_posix(), *args])
    def save(name, value):
        (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assert git('rev-parse','HEAD').decode().strip() == PIN
    changed = git('diff','--name-status',MAIN+'...'+PIN).decode().splitlines()
    allowed_m = {'docs/phases/2026-09-11-to-09-16/B.md', REL.rsplit('/',1)[0]+'/README.md'}
    assert len(changed) == 20
    for line in changed:
        mode, path = line.split('\t')
        assert (mode=='M' and path in allowed_m) or (mode=='A' and path.startswith(REL+'/')), line
    files=[line.split('\t')[1] for line in changed]
    before={f:sha((repo/f).read_bytes()) for f in files}
    blob_equal={f:sha(git('show',PIN+':'+f))==h for f,h in before.items()}
    # Historical files have exact byte protection; other text may use checkout CRLF.
    assert all(blob_equal[f] for f in files if '/historical-evidence/' in f)
    folder=repo/REL
    record=json.loads((folder/'REGISTER.json').read_text(encoding='utf-8'))
    hist=json.loads((folder/'historical-evidence/08-independent.json').read_text(encoding='utf-8'))
    assert record['source_commit']=='d088e2c7deda9c505c094fd48d6f90bcd7f52807'
    assert record['receipt_commit']=='2e2f685faf5520181cdd00cde2cd5030e75e67e2'
    run([sys.executable,'-B',REL+'/verify_register.py'],'verify-register')
    original_paths=git('ls-tree','-r','--name-only',record['source_commit'],'--',A_REL).decode().splitlines()
    paths=[e['path'] for e in hist['git_blob_checks']]
    assert len(paths)==len(set(paths))==76 and set(paths)==set(original_paths)
    assert len(record['historical_files'])==10
    assert set(record['historical_files'])=={f.name for f in (folder/'historical-evidence').iterdir() if f.is_file()}
    index=record['input_files']
    assert len(index)==len({e['path'] for e in index})==18
    assert {e['path'] for e in index}=={f for f in original_paths if '/captures/' in f}
    manifest=git('show',record['source_commit']+':'+A_REL+'/payload/MANIFEST.sha256.json')
    assert sha(manifest)==record['payload_manifest_sha256']
    receipt_change=git('diff','--name-status',record['source_commit'],record['receipt_commit']).decode().splitlines()
    assert receipt_change==['A\t'+record['receipt_path']]
    receipt=git('show',record['receipt_commit']+':'+record['receipt_path']).decode('utf-8')
    assert record['source_commit'] in receipt and '可接收' in receipt
    source_meta=[]
    reader_hist=json.loads((folder/'historical-evidence/02-reader.txt').read_text(encoding='utf-8'))
    for s in hist['segments']:
        capture=s['acquisition']
        meta=json.loads(git('show',record['source_commit']+':'+A_REL+'/payload/captures/'+capture+'/metadata.json'))
        assert meta['acquisition_id']==capture and meta['coordinates_m'] is None
        assert meta['source_kind']=='hardware-audio' and meta['evidence_level']=='diagnostic'
        r=next(x for x in reader_hist['segments'] if x['acquisition_id']==capture)
        assert (r['samples'],r['first_sample_id'],r['last_sample_id'])==(s['groups'],s['first_id'],s['last_id'])
        for name,expected in r['file_sha256'].items():
            item=next(x for x in index if x['path']==A_REL+'/payload/captures/'+capture+'/'+name)
            assert item['sha256']==expected
        source_meta.append(dict(acquisition=capture,groups=s['groups'],first_id=s['first_id'],last_id=s['last_id'],coordinates_m=meta['coordinates_m'],source_kind=meta['source_kind'],evidence_level=meta['evidence_level']))
    logs={}
    for name,count in [('05-reader-tests.txt',47),('06-export-tests.txt',8),('07-gate-tests.txt',9)]:
        body=(folder/'historical-evidence'/name).read_text(encoding='utf-8')
        assert re.search(r'Ran '+str(count)+r' tests\b',body) and body.rstrip().endswith('OK')
        logs[name]=dict(historical_tests=count,rerun_this_review=False)
    old=(folder/'historical-evidence/independent_review.py').read_text(encoding='utf-8')
    new=(folder/'replay_independent.py').read_text(encoding='utf-8')
    marker="snapshot=json.loads((P/'build-snapshot/manifest.json').read_text())"
    old_compute=old[old.index(marker):old.index("(E/'08-independent.json').write_text")]
    new_compute=new[new.index(marker):new.index("with args.output.open('x',encoding='utf-8')")]
    assert old_compute==new_compute
    assert ast.dump(ast.parse(old_compute),include_attributes=False)==ast.dump(ast.parse(new_compute),include_attributes=False)
    assert old[old.index("print('Git blobs'"):]==new[new.index("print('Git blobs'"):]
    compile(new,'replay_independent.py','exec')
    (out/'replay-adaptation.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='historical independent_review.py',tofile='replay_independent.py')),encoding='utf-8')
    run(['git','diff','--check',MAIN+'...'+PIN],'diff-check')
    links=[]
    for name in [REL+'/README.md',*allowed_m]:
        for link in re.findall(r'\]\(([^)]+)\)',(repo/name).read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'): continue
            dest=(repo/name).parent/link.split('#')[0]
            assert dest.exists(), (name,link)
            links.append(dict(source=name,target=link))
    ancestry={}
    for label,c in [('source',record['source_commit']),('receipt',record['receipt_commit'])]:
        r=subprocess.run(['git','merge-base','--is-ancestor',c,MAIN],cwd=repo,capture_output=True)
        assert r.returncode in (0,1)
        commands.append(dict(argv=['git','merge-base','--is-ancestor',c,MAIN],cwd=str(repo),exit_code=r.returncode))
        ancestry[label]=r.returncode==0
    main_delivery=git('ls-tree','-r','--name-only',MAIN,'--',A_REL).decode().splitlines()
    after={f:sha((repo/f).read_bytes()) for f in files}
    assert before==after
    assert not git('status','--porcelain').strip()
    save('checks.json',dict(status='PASS_REGISTRATION_CHECKS_ONLY',review_sha=PIN,main_checked=MAIN,
        changed_files=20,allowed_changes=changed,historical_hash_count=10,unique_original_blob_coverage=76,
        unique_capture_index=18,receipt_change=receipt_change,manifest_blob_hash=sha(manifest),capture_metadata_crosscheck=source_meta,
        historical_tests=logs,computational_region_equal=True,computational_ast_equal=True,
        computational_region_sha256=sha(old_compute.encode('utf-8')),numerical_replay_executed=False,
        replay_syntax_compiled=True,relative_links_checked=links,source_in_main=ancestry['source'],receipt_in_main=ancestry['receipt'],main_delivery_paths=main_delivery,
        checkout_files_unchanged=True,checkout_vs_blob_byte_equal=blob_equal,protected_checkout_sha256=before,
        python=platform.python_version(),no_hardware_or_h2_h3_approval=True))
    save('commands.json',commands)
    print('PASS: registration, source/capture identity, original evidence protection, replay code equivalence; no numerical replay')

if __name__=='__main__': main()
