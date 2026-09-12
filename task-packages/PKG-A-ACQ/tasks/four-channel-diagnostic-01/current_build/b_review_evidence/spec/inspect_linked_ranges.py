import sys,json
from pathlib import Path
root=Path('F:/NUEC/review-worktrees/a-ps-repair-d0ce1c2/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build')
sys.path.insert(0,str(root))
import ps_contract as pc
exe=pc.Elf32(root/'repair_ps_contract/evidence/compiled-proof/valid/four_mic_capture.elf',2)
c=exe.contract()
report=json.loads((root/'repair_ps_contract/evidence/legal-ps-02/ps_check/contract-result.json').read_text())
r=pc.validate_values(c, report['hardware'],exe.allocated+exe.loads,exe.symbol_value('end'))
print(json.dumps({'actual_archived_elf_validation':r,'stack_heap_symbols':{k:hex(v[1]) for k,v in exe.symbols.items() if 'stack' in k.lower() or 'heap' in k.lower()},'heap_stack_sections':[s for s in exe.allocated if s['name'] in ('.heap','.stack')]},indent=2))
