import sys, subprocess, json, hashlib, gzip
from pathlib import Path
import numpy as np
root = Path(sys.argv[1]).resolve()
sha = 'b8c5e87f6cb1054c2684719310f02f36c83ac731'
parent = 'bb82de16a33751fb684243a19132dbb6b5736d91'
rel = 'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01'
ext = root / rel
git = 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def g(*a):
    return subprocess.check_output([git, '-c', f'safe.directory={root.as_posix()}', '-C', str(root), *a])
def read(p): return json.loads(p.read_bytes())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
diff = g('diff', '--name-status', parent, sha).decode().splitlines()
assert len(diff) == 86 and all(x.startswith('A\t'+rel+'/') for x in diff)
for row in diff:
    name = row.split('\t')[1]
    assert (root/name).read_bytes() == g('show', sha+':'+name), name
manifest=read(ext/'SHA256SUMS.json')
assert len(manifest)==85
assert {p.relative_to(ext).as_posix() for p in ext.rglob('*') if p.is_file()} == set(manifest)|{'SHA256SUMS.json'}
for name, v in manifest.items():
    assert digest(ext/name)==v['sha256'] and (ext/name).stat().st_size==v['bytes']
old=read(ext.parent/'SHA256SUMS.json')
assert len(old)==155
for name,v in old.items():
    assert digest(ext.parent/name)==v['sha256']
prep=read(ext/'PREPARATION-SHA256.json')['files']
assert len(prep)==14
mapping=read(ext/'PREPARATION-HISTORY.json')['paths']
for v in prep: assert digest(ext/mapping.get(v['path'],v['path']))==v['sha256']
b=ext/'evidence/run01'
prepared=read(b/'preparation/prepared-sha256.json')
for name in ['inputs.mem','expected.npy','job-count.mem','selection.json']:
    assert digest(b/'vectors'/name)==prepared['vectors/'+name]['sha256']
assert int((b/'vectors/job-count.mem').read_text(),10)==817
c=read(b/'configuration-check.json')
assert digest(b/'reports/ss_fft29.xci')==c['actual_xci_sha256']==c['old_xci_sha256']
assert digest(b/'sources_used/tb_fft29.sv')==c['compiled_tb_sha256']
assert digest(b/'reports/ss_fft29-sim-wrapper.vhd')==c['compiled_wrapper_sha256']
log=(b/'simulation/compile.log').read_text()
for key in ['actual_compiled_tb','actual_compiled_wrapper']:
    assert c[key].replace('\\','/') in log
ip=read(b/'reports/ss_fft29.xci')['ip_inst']
assert ip['component_reference']=='xilinx.com:ip:xfft:9.1' and ip['ip_revision']=='15'
with gzip.open(b/'simulation/outputs.csv.gz','rt') as f: rows=np.loadtxt(f,delimiter=',',dtype=np.int64)
with gzip.open(b/'simulation/status.csv.gz','rt') as f: status=np.loadtxt(f,delimiter=',',dtype=np.int64)
expected=np.load(b/'vectors/expected.npy',allow_pickle=False)
assert rows.shape==(817*1024,4) and expected.shape==(817,1024,2)
assert np.array_equal(rows[:,0],np.repeat(np.arange(817),1024))
assert np.array_equal(rows[:,1],np.tile(np.arange(1024),817))
assert np.array_equal(rows[:,2:].reshape(expected.shape),expected)
assert status.shape==(817,3) and np.array_equal(status[:,0],np.arange(817)) and not status[:,2].any()
sel=read(b/'vectors/selection.json'); historical=read(ext.parent/'evidence/run01/vectors/selection.json')
assert len(set(sel['selected_cases']))==136 and len(set(historical['selected_cases']))==60
assert not set(sel['selected_cases'])&set(historical['selected_cases'])
assert set(sel['selected_cases'])|set(historical['selected_cases'])==set(range(196))
assert [(j['case'],j['channel']) for j in sel['jobs'][:-1]]==[(c,ch) for c in sel['selected_cases'] for ch in range(6)]
print(json.dumps({'audit_sha':sha,'status':'PASS','added_git_blobs':86,'manifest_entries':85,'historical_entries':155,'preparation_entries':14,'unique_new_fft':816,'new_jobs_in_archive':817,'integer_components':int(expected.size),'mismatches':0,'overflow':0,'new_XSim_runs_by_B':0,'python':sys.version,'numpy':np.__version__},indent=2))
