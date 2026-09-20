import pathlib,json,hashlib,subprocess,collections
root=pathlib.Path('F:/NUEC/review-worktrees/s1-8f708e4'); rel='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917'; p=root/rel; out=pathlib.Path('F:/NUEC/review-evidence/s1-8f708e4/standards')
git='C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def g(*args):return subprocess.check_output([git,'-c','core.quotepath=false','-c','safe.directory='+str(root),'-C',str(root),*args])
changes=g('diff','--name-status','02b578c730c539e7fb45e11386567f28ffe7ab71...HEAD').decode().splitlines()
d=p/'delivery-01'; m=json.loads((d/'FINAL-SHA256.json').read_text(encoding='utf-8'))['files']; bad=[n for n,h in m.items() if hashlib.sha256((d/n).read_bytes()).hexdigest()!=h]
actual={x.relative_to(d).as_posix() for x in d.rglob('*') if x.is_file()}
deps=json.loads((d/'dependencies.json').read_text(encoding='utf-8')); depbad=[n for n,h in deps.items() if hashlib.sha256((root/n.replace('\\','/')).read_bytes()).hexdigest()!=h]
tracked=g('ls-tree','-r','HEAD','--',rel).decode().splitlines(); blobbad=[]
for row in tracked:
 meta,name=row.split('\t'); data=(root/name).read_bytes(); obj=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 if obj!=meta.split()[2]:blobbad.append(name)
md=json.loads((d/'c-scene-20260917-01/metadata.json').read_text(encoding='utf-8')); rec=json.loads((d/'actual-record.json').read_text(encoding='utf-8'))
r=dict(sha=g('rev-parse','HEAD').decode().strip(),change_counts=dict(collections.Counter(x.split('\t')[0] for x in changes)),outside_scope=[x for x in changes if not x.split('\t')[-1].startswith(rel+'/')],tracked_files=len(tracked),git_byte_mismatches=blobbad,final_manifest_entries=len(m),manifest_mismatches=bad,delivery_extra=sorted(actual-set(m)),dependency_count=len(deps),dependency_mismatches=depbad,source_record_equal=md['source_placement_record']==rec,failure_records=[x.relative_to(p).as_posix() for x in p.rglob('failure.json')])
(out/'independent-identity.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))


