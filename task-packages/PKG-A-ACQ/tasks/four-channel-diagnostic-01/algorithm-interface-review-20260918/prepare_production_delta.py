"""Prepare independent exact-integer test inputs; no DUT or engineering execution."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PIN='f08556d01821d6c3c8204fdac2c38f53b2107c05'
BASE='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
SERVICES='capture_dma_cache_copy accepted_row_frame mean_two_windows fft8 fixed4 gate_power_state cross_mask_phat conjugate_ifft6 lag doa_cordic_tracker rom_control das_two_beams config_status_commit arbitration_cdc_reset output_backpressure audit_drain'.split()

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    def save(name,data):
        (out/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    save('command.json',dict(argv=sys.argv,python=sys.version,cwd=str(Path.cwd()),pin=PIN))
    raw=subprocess.check_output(['git','show',PIN+':'+BASE+'service-budget-20260921.json'])
    (out/'pinned-service-budget.json').write_bytes(raw)
    budget=json.loads(raw)
    assert [s['id'] for s in budget['services']]==SERVICES
    assert all(s['cycles_per_hop'] is None for s in budget['services'])
    assert budget['memory']['whole_system_peak_bytes'] is None
    # Direct hand-calculated ties, signs and maximum rounding overflow.
    anchors={8:0,24:2,40:2,-8:0,-24:-2,-40:-2,(1<<28)-1:1<<24,-(1<<28):-(1<<24)}
    for x,y in anchors.items(): assert round(Fraction(x,16))==y
    values=set(anchors)
    for q in (-16777216,-17,-2,-1,0,1,2,17,16777215):
        for r in range(16):
            x=q*16+r
            if -(1<<28)<=x<(1<<28): values.add(x)
    rows=[]
    for x in sorted(values):
        y=round(Fraction(x,16));valid=-(1<<24)<=y<(1<<24)
        rows.append(dict(input_s29=x,expected_integer=y,output_s25=y if valid else None,
                         overflow=not valid,remainder_mod16=x%16,
                         kind='tie' if x%16==8 else 'non_tie'))
    assert {r['remainder_mod16'] for r in rows}==set(range(16))
    assert any(r['overflow'] for r in rows)
    save('fixed4-prepared-vectors.json',rows)
    save('result.json',dict(status='PREPARATION_ONLY_NOT_RTL_NOT_BOARD',
         vector_count=len(rows),hand_anchors=len(anchors),residue_classes=16,
         service_ids_checked=len(SERVICES),actual_bounds_known=0,
         input_sha256=hashlib.sha256(raw).hexdigest(),
         source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         numeric_default_changed=False,RTL='NOT_RUN',AMD='NOT_RUN',ARM='NOT_RUN',
         board='NOT_RUN',realtime='REALTIME_BLOCKED'))
    print('PREPARATION_ONLY vectors=',len(rows),'services=',len(SERVICES))

if __name__=='__main__': main()
