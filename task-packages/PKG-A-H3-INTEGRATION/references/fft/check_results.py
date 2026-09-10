"""Check complete probe output and report measured integer cycle differences."""
import argparse, csv, json, math
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--vectors',type=Path,required=True)
p.add_argument('--sim',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
ref=json.loads((a.vectors/'reference.json').read_text())
rows=list(csv.reader((a.sim/'outputs.csv').open()))
assert len(rows)==22*1024, len(rows)
assert [r[2:] for r in rows[21*1024:22*1024]] == [r[2:] for r in rows[9*1024:10*1024]], 'backpressure changed data'
errors=[]
for row,expected_index in zip(rows,range(22*1024)):
    job,index,re,im=map(int,row)
    assert (job,index)==divmod(expected_index,1024)
    expected=ref[job][index]
    errors.extend([abs(re-expected[0]),abs(im-expected[1])])
# A priori engineering smoke-test tolerance, not H3/algorithm acceptance.
assert max(errors)<=16, max(errors)
times=[list(map(int,r)) for r in csv.reader((a.sim/'cycles.csv').open())]
assert len(times)==22
for j,cfg,first,last,fo,lo in times:
    assert cfg<=first<=last<fo<=lo
    if j<21: assert last-first==1023 and lo-fo==1023
baseline=[r[5]-r[1]+1 for r in times[:21]]
assert len(set(baseline))==1
intervals=[times[j+1][1]-times[j][1] for j in range(20)]
assert len(set(intervals))==1
result=dict(status='PASS_IP_PROBE_NOT_H3',jobs=22,complex_outputs=len(rows),
    max_component_error_codes=max(errors),rms_component_error_codes=math.sqrt(sum(v*v for v in errors)/len(errors)),
    probe_tolerance_codes=16,processing_clock_target_hz=100000000,
    config_to_last_output_inclusive_cycles=baseline[0],
    first_input_to_first_output_cycles=times[0][4]-times[0][2],
    measured_serial_config_interval_cycles=intervals[0],
    scheduled_21_transform_cycles=21*intervals[0],
    hop_cycles_floor=100000000*512//48000,
    stressed_config_to_last_output_inclusive_cycles=times[-1][5]-times[-1][1]+1,
    limitation='No arbitrary-backpressure bound, full PHAT validation, post-route or hardware timing claim.')
a.out.parent.mkdir(parents=True,exist_ok=True)
with a.out.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
