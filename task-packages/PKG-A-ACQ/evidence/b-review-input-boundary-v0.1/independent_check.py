"""B independent format-boundary checks; not real PDM or DMA acceptance."""
from fractions import Fraction
from pathlib import Path
import json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'task-packages/PKG-B-ALG/payload/model/python'))
from audio_frames import adapt_six_mic_baseline,BASELINE_POSITIONS

def find(obj,key):
    found=[]
    if isinstance(obj,dict):
        if key in obj:found.append(obj[key])
        for v in obj.values():found.extend(find(v,key))
    elif isinstance(obj,list):
        for v in obj:found.extend(find(v,key))
    return found
def value(x):return x.get('value') if isinstance(x,dict) else x
bd=json.loads((ROOT/'task-packages/PKG-A-ACQ/evidence/input-boundary-v0.1/source-snapshot/system.bd').read_text(encoding='utf-8'))
expected={'PCW_FPGA0_PERIPHERAL_FREQMHZ':100,'PCW_ACT_FPGA0_PERIPHERAL_FREQMHZ':100,'c_include_sg':0,'c_s_axis_s2mm_tdata_width':32,'c_m_axi_s2mm_data_width':64}
actual={}
for key,wanted in expected.items():
    values=[float(value(x)) for x in find(bd,key)]
    assert values and all(x==wanted for x in values),(key,values)
    actual[key]=values
raw=np.array([0x8000,0xffff,0,0x7fff],dtype=np.uint16)
decoded=raw.view(np.int16).astype(np.int32)
assert decoded.tolist()==[-32768,-1,0,32767]
assert [float(Fraction(int(x),2**23)) for x in decoded]==[-1/256,-2**-23,0,32767/2**23]
assert float(Fraction(8388607,2**23))==1-2**-23
x=np.tile(np.array([2.,-3.5,0.,.25]),(6,1))
segment=adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=BASELINE_POSITIONS,source_id='B-format-boundary-check',source_sha256='0'*64,first_sample_id=7)
np.testing.assert_array_equal(segment.samples,x.T)
np.testing.assert_array_equal(segment.sample_ids,[7,8,9,10])
assert np.max(np.abs(segment.samples))>1
print(json.dumps(dict(status='PASS',configured_bd_values=actual,signed16_codes=decoded.tolist(),
    six_mic_float_gain_preserved=True,hardware_acceptance=False),ensure_ascii=False))
