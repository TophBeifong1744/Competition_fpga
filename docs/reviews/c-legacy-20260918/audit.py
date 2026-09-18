import hashlib, io, json, pathlib, subprocess, sys, zipfile
R = pathlib.Path(sys.argv[1]).resolve()
W = pathlib.Path(sys.argv[2]).resolve()
W.mkdir(parents=True, exist_ok=False)
G = ['git', '-c', 'safe.directory='+R.as_posix(), '-C', str(R)]
BASE = '5cfa02e51af44bb5c930babf732ddc864a1ab6cd'
CAND = '1731522f80ed0b970c63c8a3b019b9ba281d6ca8'
def git(*a): return subprocess.check_output(G+list(a))
def sha(b): return hashlib.sha256(b).hexdigest()
out={'base':BASE,'candidate':CAND,'packages':{},'reference_drift':[]}
for pid in ['WP-A0','WP-S1','3D-P2','3D-P4','REL6-001']:
    prefix='task-packages/'+pid+'/'
    raw=git('show',CAND+':'+prefix+'evidence/files.json')
    m=json.loads(raw.decode('utf-8-sig'))
    entries=m['payload']+m['references']
    errors=[]
    for e in entries:
        p=prefix+e.get('package_path',e.get('snapshot_path',''))
        b=git('show',BASE+':'+p)
        if sha(b)!=e['sha256']: errors.append(p)
        if b!=git('show',CAND+':'+p): errors.append('candidate changed: '+p)
    out['packages'][pid]={'manifest_sha256':sha(raw),'checked':len(entries),'errors':errors}
    for e in m['references']:
        p=R/e['path']; expected=(R/prefix/e['snapshot_path']).read_bytes()
        if not p.exists(): reason='missing'
        elif p.read_bytes()==expected: continue
        elif p.read_bytes().replace(b'\r\n',b'\n')==expected.replace(b'\r\n',b'\n'): reason='line endings only'
        else: reason='content differs'
        out['reference_drift'].append({'package':pid,'path':e['path'],'reason':reason})
snapshot=R/'task-packages/WP-A0/evidence/reference-snapshots/archive/2026-09-07-before-materials-cleanup'
historical=json.loads((snapshot/'MANIFEST.json').read_text(encoding='utf-8-sig'))
out['historical_manifest']={'count':len(historical['files']),'mismatches':[
    {'path':e['path'],'expected':e['sha256'],'actual':sha((snapshot/e['path']).read_bytes())}
    for e in historical['files'] if sha((snapshot/e['path']).read_bytes())!=e['sha256']]}
bundle=R/'task-packages/REL6-001/evidence/reference-snapshots/deliverables/six-mic-acoustic-review-v1'
for label,args in [('rel6-snapshot',[sys.executable,str(bundle/'verify_package.py'),'--reproduced',str(R/'task-packages/REL6-001/evidence/reference-snapshots/archive/2026-09-07-six-mic-package-verification')]),('rel6-active',[sys.executable,str(R/'deliverables/six-mic-acoustic-review-v1/verify_package.py')])]:
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (W/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    out[label]={'exit':p.returncode,'output':p.stdout+p.stderr}
# Export exact committed bytes to separate checkout-free directory for final-path integrity.
dest=W/'committed'
with zipfile.ZipFile(io.BytesIO(git('archive','--format=zip',BASE,'deliverables/six-mic-acoustic-review-v1'))) as z:
    z.extractall(dest)
p=subprocess.run([sys.executable,str(dest/'deliverables/six-mic-acoustic-review-v1/verify_package.py')],capture_output=True,text=True)
out['rel6-committed']={'exit':p.returncode,'output':p.stdout+p.stderr}
fault=dest/'deliverables/six-mic-acoustic-review-v1/REPORT.md'
original=fault.read_bytes()
try:
    fault.write_bytes(original+b'\nINDEPENDENT HASH NEGATIVE CONTROL\n')
    p=subprocess.run([sys.executable,str(dest/'deliverables/six-mic-acoustic-review-v1/verify_package.py')],capture_output=True,text=True)
    assert p.returncode!=0 and 'hash mismatch: REPORT.md' in p.stdout+p.stderr
    out['negative_control']={'exit':p.returncode,'output':p.stdout+p.stderr}
finally:
    fault.write_bytes(original)
out['p2_arithmetic']={'six_mic_pairs':6*5//2,'transforms':6+6*5//2,'pcm_mbit_s':6*48000*24/1e6,'container_MB_s':6*48000*4/1e6,'one_hour_GB':6*48000*4*3600/1e9,'mask_coeff_MB':32768*3*15*24/8/1e6}
(W/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='reference_drift'},ensure_ascii=False,indent=2))
