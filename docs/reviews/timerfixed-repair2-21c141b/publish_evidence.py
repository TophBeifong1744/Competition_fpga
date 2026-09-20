import hashlib,json,shutil,subprocess
from pathlib import Path
OUT=Path(__file__).parent
ROOT=Path('F:/NUEC/review-worktrees/timerfixed-r1-integration')
DEST=ROOT/'docs/reviews/timerfixed-repair2-21c141b'
GIT='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def git(*args):return subprocess.run([GIT,'-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args],capture_output=True)
assert json.loads((OUT/'integration-run01/result.json').read_text())['status']=='PASS_R1_AUTHOR_REGRESSION_NOT_B_APPROVAL'
entry='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01'
assert git('diff','--cached','--exit-code','21c141b223936730c2ce5139624fcedb412adafb','--',entry).returncode==0
check=git('diff','--cached','--check')
import gzip
(OUT/'integration-whitespace.txt.gz').write_bytes(gzip.compress(check.stdout+check.stderr))
(OUT/'integration-summary.json').write_text(json.dumps({'status':'PASS_LIMITED','package_index_identical_to_reviewed_SHA':True,'manifest':'267+209+87 PASS','regression':'94 Python, including 14 Tcl simulations PASS','whitespace_exit':check.returncode,'whitespace_notice':'Frozen original map/init/log bytes retained, not counted as clean check','initial_import_failure':'Windows filename too long; repeated with core.longpaths=true, successful'},indent=2)+'\n')
assert not DEST.exists()
shutil.copytree(OUT,DEST)
(DEST/'.gitattributes').write_text('* -text\n')
files={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST/'B-EVIDENCE-SHA256.json').write_text(json.dumps({'review_sha':'21c141b223936730c2ce5139624fcedb412adafb','files':files},indent=2)+'\n')
print('Copied B evidence',len(files),'files plus manifest')
