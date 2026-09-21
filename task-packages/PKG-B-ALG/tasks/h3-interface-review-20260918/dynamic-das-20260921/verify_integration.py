import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from delay_rom import DelayROM
from verify_dynamic import run_stream, offline


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    meta=json.loads((a.rom.parent/'result.json').read_text())
    rom=DelayROM(a.rom,meta['rom_sha256'])
    path=a.repo/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/fixed_golden.py'
    spec=importlib.util.spec_from_file_location('integration_fg',path);fg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fg;spec.loader.exec_module(fg)
    for angle in range(-46080,46080):assert rom.lookup(angle)==tuple(fg.delay_q12_from_angle(angle))
    rejects=0
    for bad in (True,0.0,-46081,46080):
        try:rom.lookup(bad)
        except ValueError:rejects+=1
        else:raise AssertionError('invalid angle accepted')
    try:DelayROM(a.rom,'0'*64)
    except ValueError:rejects+=1
    else:raise AssertionError('wrong hash accepted')
    # Existing tracker, unchanged acquisition/step/HOLD configuration. Direction
    # ready_sample maps to available_emit_sample=ready+8 as in old audio contract.
    tracker=fg.FixedTracker();rows={};history=[]
    for i in range(1,33):
        ready=i*512
        accepted=i<=9 or i>=30
        angle=0 if i<=5 else 19*256
        state=tracker.update(ready,angle if accepted else None,accepted)
        emit=ready+8
        if state['fresh_valid']:
            control=dict(state='LOCKED',delays=rom.lookup(state['angle_q8_deg']),valid_through=state['valid_through_sample']+8)
        elif state['state']=='HOLD':control=dict(state='HOLD')
        else:control=dict(state='SEARCH')
        rows[emit]=control;history.append(dict(ready=ready,emit=emit,tracker=state,control=control))
    rng=np.random.default_rng(2026092108)
    pcm=rng.integers(-2**23,2**23,size=(4,18000),dtype=np.int64)
    expected,segments=offline(pcm,rows,480)
    results=[]
    for chunk in (127,512):
        actual,traces,engine=run_stream(pcm,rows,chunk,480)
        assert np.array_equal(actual,expected)
        assert engine.max_beams<=2 and engine.max_history<=17
        results.append(dict(chunk=chunk,sha256=hashlib.sha256(actual.astype('<i4').tobytes()).hexdigest(),events=engine.events))
    first=next(x for x in history if x['tracker']['fresh_valid'])
    first_emit=first['emit'];single=np.concatenate([np.zeros(8,dtype=np.int64),pcm[0]])
    assert np.array_equal(actual[:first_emit+1],single[:first_emit+1])
    assert any(x['tracker']['state']=='HOLD' for x in history)
    assert any(x['tracker']['state']=='SEARCH' for x in history)
    (a.out/'controls.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
    (a.out/'cases.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    result=dict(status='AUTHOR_INTEGER_CONTROL_PASS',rom_lookups=92160,invalid_cases=rejects,tracker_updates=len(history),chunk_cases=2,first_fresh_emit=first_emit,pcm_kind='mathematical S24 fixture; no acoustic accuracy or gain',scope='existing tracker + ROM + candidate DAS; no gate/DOA/audio device or session transaction')
    (a.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)


if __name__=='__main__':main()
