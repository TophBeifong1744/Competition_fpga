"""Check budget arithmetic and bind a new package manifest; no Git writes."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
target=root/'PACKAGE-SHA256.json'
if target.exists():raise ValueError('Manifest exists; preserve it')
parts=[32768,4096,16416,4104,8192,4096,160,4096,16128,1024]
limit=100000000*512//48000;slots=4*7366+6*7406
assert (sum(parts),limit,slots,limit-slots,48000*32)==(91080,1066666,73900,992766,1536000)
budget=dict(logical_bytes=sum(parts),strict_hop_cycle_limit=limit,historical_transform_slots=slots,
    arithmetic_difference_not_proven_margin=limit-slots,raw_bytes_per_second=48000*32,
    total_cycles=None,status='REALTIME_BLOCKED',actual_check='integer arithmetic only')
(root/'evidence/budget-arithmetic.json').write_text(json.dumps(budget,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bindings=json.loads((root/'evidence/run02/source-sha256.json').read_text(encoding='utf-8'))
for name,digest in bindings.items():assert sha(root/'source'/name)==digest,(name,'changed after run02')
result=json.loads((root/'evidence/run02/checks.json').read_text(encoding='utf-8'))
assert result['passed']==28 and result['failed']==0
data=dict(scope='Incremental software logic package; no production/RTL/board approval',
    files={p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p!=target})
target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print('PACKAGE_SHA256',sha(target))
