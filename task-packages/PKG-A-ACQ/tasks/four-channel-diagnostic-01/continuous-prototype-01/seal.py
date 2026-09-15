"""One-time local evidence seal; no git writes and no hardware operations."""
import hashlib,json,sys
from pathlib import Path
import run as c
root=c.HERE
dependency=root/'dependency-snapshot'
dependency.mkdir()  # refuse overwriting a previous seal
deps={}
for name in ('build_current.py','build_hw.tcl','ps_contract.py','test_build_current.py'):
    source=root.parent/'current_build'/name;c.copy(source,dependency/name)
    deps[str(source)]=c.safe.sha(source)
c.write(root/'DEPENDENCIES.json',deps)
old=root.parent/'batches/center-target-20260914'
old_manifest=json.loads((old/'PACKAGE-SHA256.json').read_text(encoding='utf-8'))
bad=[name for name,digest in old_manifest.items() if c.safe.sha(old/name)!=digest]
c.safe.require(not bad,'previous frozen batch changed: '+str(bad))
c.write(root/'PRESERVATION.json',{'previous_frozen_batch':str(old),'previous_files_checked':len(old_manifest),'changed':bad,
    'original_one_check':'delivery-01/evidence/build/original-integrity.json',
    'rollback':'delivery-01/rollback-short/SHA256.json','no_board_operation':True,'no_git_write':True})
out=root/'package-check';out.mkdir()
c.run([sys.executable,'-B',root/'check_release.py','--release',root/'delivery-01/release'],out,'release-check')
c.manifest(out)
c.write(root/'PACKAGE-SHA256.json',{p.relative_to(root).as_posix():c.safe.sha(p) for p in root.rglob('*') if p.is_file() and p.name!='PACKAGE-SHA256.json' and '__pycache__' not in p.parts})
print('PACKAGE_SEALED_NOT_BOARD_OR_INDEPENDENT_ACCEPTANCE')
