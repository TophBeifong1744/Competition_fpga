import hashlib,json,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path('F:/NUEC/review-worktrees/a-ps-repair-d0ce1c2')
T=R/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01';C=T/'current_build'
OLD='050d06f5dc6fed4fa476e72fa416e9736bc7fef3';NEW='d0ce1c28aac3e101a262036b2321f4170d34f45c'
def git(*args):return subprocess.check_output(['git','-c','core.longpaths=true','-c','safe.directory='+R.as_posix(),'-C',str(R),*args])
def tree(ref):
    result={}
    for row in git('ls-tree','-rz',ref).split(b'\0'):
        if row:
            info,name=row.split(b'\t');result[name.decode()]=info.split()[2].decode()
    return result
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a,b=tree(OLD),tree(NEW)
changed=[n for n in b if a.get(n)!=b[n]]
assert len(changed)==714 and not set(a)-set(b)
assert all(n.startswith('task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build/') for n in changed)
for n in changed:
    raw=(R/n).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==b[n],n
manifest=json.loads((C/'repair_ps_contract/REPAIR-MANIFEST.json').read_text())['files']
assert len(manifest)==713
for x in manifest:
    p=C/x['path'];assert p.stat().st_size==x['bytes'] and digest(p)==x['sha256'].lower(),x['path']
old_manifest=json.loads((C/'ENVELOPE-SHA256.json').read_text())['files']
old_unchanged=[];old_changed=[]
for x in old_manifest:
    p=C/x['path']
    (old_unchanged if digest(p)==x['sha256'].lower() else old_changed).append(x['path'])
assert len(old_unchanged)==90 and set(old_changed)=={'.gitattributes','.gitignore','README.md','build_current.py'}
frozen=json.loads((T/'DELIVERY-MANIFEST-20260912.json').read_text())['files']
assert len(frozen)==189
for x in frozen:
    p=R/x['path'];assert p.stat().st_size==x['bytes'] and digest(p)==x['sha256'].lower()
    assert a[x['path']]==b[x['path']]
assert all(a[n]==b[n] for n in a if '/current_build/evidence/' in n)
matrix=[]
for k in ['matrix01','matrix02','matrix03']:
    m=json.loads((C/f'repair_ps_contract/evidence/{k}/matrix-result.json').read_text())
    matrix.append({'name':k,'case_count':len(m['cases']),'all_expectations':all(x['expectation_met'] for x in m['cases']),'cases':[{f:x.get(f) for f in ['case','expected_pass','result','error','expectation_met','native_exit_code']} for x in m['cases']]})
assert not matrix[0]['all_expectations'] and matrix[1]['all_expectations'] and matrix[2]['all_expectations'] and matrix[2]['case_count']==14
sys.path.insert(0,str(C));import ps_contract as pc
proof=C/'repair_ps_contract/evidence/compiled-proof'
obj=pc.Elf32(proof/'valid/ps_build_unit.o',1);exe=pc.Elf32(proof/'valid/four_mic_capture.elf',2)
rejected=pc.Elf32(proof/'rejected/ps_build_unit.o',1)
report=json.loads((C/'repair_ps_contract/evidence/legal-ps-02/ps_check/contract-result.json').read_text())
assert obj.contract()==exe.contract()==report['compiled_values']
assert rejected.contract()['BASE']==0x00100000
values=pc.validate_values(exe.contract(),report['hardware'],exe.allocated+exe.loads,exe.symbol_value('end'))
assert values==report['values']
for name in ['ps_build_unit.o','four_mic_capture.elf','four_mic_capture.map']:
    assert digest(proof/'valid'/name)==report['bindings_sha256']['ps_check/'+name]
exact=json.loads((C/'repair_ps_contract/evidence/exact-legacy-after/preflight.json').read_text())
source_hashes=[v for n,v in exact['protected_sha256'].items() if n.endswith('main_four_capture.c')]
assert source_hashes==['5a21c65da0f29707fafe64e7d1fe4c7382ef6d23e09598464a52bd0b0d394c32']
old_sources=list((C/'repair_ps_contract/legacy-counterexample-01').rglob('main_four_capture.c'))
assert any(digest(p)==source_hashes[0] for p in old_sources)
plan=json.loads((C/'evidence/run04/preflight.json').read_text())
deps={k:{'path':plan[k],'exists':Path(plan[k]).exists()} for k in ['project','vivado','gcc','bsp','bsp_xsa','ps_source']}
result={'review_sha':NEW,'old_sha':OLD,'changed_files_verified':714,'repair_manifest_entries_verified':713,'old_manifest_unchanged_entries':90,'old_manifest_changed_entries':old_changed,'frozen_unchanged':189,'old_evidence_unchanged':True,'matrix_archive_audit':matrix,'compiled_proof_values':values,'compiled_proof_contract':exe.contract(),'rejected_object_BASE':rejected.contract()['BASE'],'exact_legacy_source_sha256':source_hashes[0],'dependencies':deps,'full_compile_or_hw_rerun':False,'git_head':git('rev-parse','HEAD').decode().strip()}
out=E/('04-evidence-verification.json' if len(sys.argv)==1 else 'post-merge-evidence-verification.json')
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS 714 changed blobs, 713 manifest entries, 90 unchanged old entries,189 frozen; real archived object/ELF values and matrix14 audit')
