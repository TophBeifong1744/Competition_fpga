import gzip,hashlib,json,shutil,subprocess
from pathlib import Path
OUT=Path(__file__).parent
ROOT=Path('F:/NUEC/review-worktrees/s1-integration')
DEST=ROOT/'docs/reviews/s1-8f708e4'
GIT='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
P='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917'
def git(*args):return subprocess.run([GIT,'-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args],capture_output=True)
assert json.loads((OUT/'integration-check.json').read_text())['status']=='PASS_OFFLINE_NOT_B_ACCEPTANCE'
assert git('diff','--cached','--exit-code','8f708e42caf32c1de6f30726298e3edf0e1970b6','--',P).returncode==0
deps=['task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/export_four.py','task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/test_export.py','task-packages/PKG-B-ALG/payload/model/python/h1_reader.py','task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build/ps_contract.py']
for dep in deps:assert git('show','8f708e42caf32c1de6f30726298e3edf0e1970b6:'+dep).stdout==(ROOT/dep).read_bytes(),dep
check=git('diff','--cached','--check')
(OUT/'integration-whitespace.txt.gz').write_bytes(gzip.compress(check.stdout+check.stderr))
audit={'package_index_identical':True,'package_files':186,'integration_archive_check':'PASS','unchanged_dependencies':deps,'whitespace_exit':check.returncode,'whitespace_warning_lines':sum(b'whitespace' in line or b'blank line' in line for line in check.stdout.splitlines()),'scope':'Only S1 directory plus independent B review; no historical gate deployed'}
(OUT/'integration-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
shutil.copytree(OUT,DEST)
(DEST/'.gitattributes').write_text('* -text\n')
files={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST/'B-EVIDENCE-SHA256.json').write_text(json.dumps({'review_sha':'8f708e42caf32c1de6f30726298e3edf0e1970b6','files':files},indent=2)+'\n')
print(json.dumps(audit));print('B evidence',len(files),'plus manifest')
