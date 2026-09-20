"""Offline oracle/replay only: no DMA driver, ready/valid or acoustic decision."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

PACKAGE = Path(__file__).resolve().parents[1]
REPO = next(p for p in PACKAGE.parents if (p / 'docs/team-workflow.md').is_file())
TASK = REPO / 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01'
sys.path.insert(0, str(TASK / 'source'))
sys.path.insert(0, str(REPO / 'task-packages/PKG-B-ALG/payload/model/python'))
from export_four import export, decode, RECORD
from h1_reader import ReaderSession
from audio_frames import adapt_h1, iter_frames, framing_summary

S1 = TASK / 'batches/background-target-stop-20260917/delivery-01/c-scene-20260917-01'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def synthetic(n, *, gap=None, clip=None, first=2**53+17):
    ids = np.arange(n, dtype=np.uint64) + np.uint64(first)
    if gap is not None:
        ids[gap:] += np.uint64(7)
    pcm = np.column_stack([np.arange(n)*k + b for k,b in [(1,-20000),(3,40000),(-5,100000),(7,-150000)]]).astype('<i4')
    raw = b''.join(RECORD.pack(int(i)&0xffffffff,int(i)>>32,*map(int,row), 4 if j==clip else 0,0)
                   for j,(i,row) in enumerate(zip(ids,pcm)))
    return raw

def copy_slots(raw):
    """Two alternating 250-group slots; copy before overwrite/free simulation."""
    slots=[bytearray(8000),bytearray(8000)]
    chunks=[]
    packets=[]
    for k,start in enumerate(range(0,len(raw),8000)):
        block=raw[start:start+8000];slot=k%2
        slots[slot][:len(block)]=block
        chunks.append(bytes(slots[slot][:len(block)]))
        packets.append({'packet':k,'slot':slot,'row_start':start//32,'groups':len(block)//32})
        slots[slot][:]=b'\xa5'*8000
    replay=b''.join(chunks)
    if replay != raw:
        raise AssertionError('slot copy mutated after free/reuse')
    return replay,packets

def inspect_record(record, raw, session):
    segment=adapt_h1(record)
    u=np.frombuffer(raw,dtype='<u4').reshape(-1,8)
    pcm=u[:,2:6].view('<i4')
    frames=[];arrays={}
    for f in iter_frames(segment):
        expected=pcm[f.row_start:f.row_stop].T.copy()
        # Power-of-two PCM conversion is exact here; independent slice/order oracle.
        actual=np.rint(f.samples*2**23).astype('<i4')
        if not np.array_equal(actual,expected):
            raise AssertionError('PCM/channel/frame alignment mismatch')
        if int(record.sample_ids[f.row_stop-1])-int(record.sample_ids[f.row_start])!=1023:
            raise AssertionError('frame crossed discontinuity')
        packets=list(range(f.row_start//250,(f.row_stop-1)//250+1))
        row={'session_id':session,'interval_id':f.interval_index,'frame_id':f.index,
             'reset_before':f.reset_before,'row_start':f.row_start,'row_stop':f.row_stop,
             'first_sample_id':str(f.first_sample_id),'last_sample_id':str(f.last_sample_id),
             'packet_indices':packets,'slot_sequence':[k%2 for k in packets],
             'pcm_channel_major_i32_sha256':digest(actual.astype('<i4').tobytes())}
        frames.append(row)
        if session!='s1':
            arrays[session+'_frame_'+str(f.index)]=actual
    summary=framing_summary(segment)
    return {'session_id':session,'groups':len(pcm),'raw_sha256':digest(raw),
            'frames':frames,'summary':summary},arrays

def generate(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    cases=[];arrays={}
    definitions=[('short1023',1023,None,None,[(0,1023)]),
                 ('exact1024',1024,None,None,[(0,1024)]),
                 ('two_hops2048',2048,None,None,[(0,2048)]),
                 ('cross_packets3000',3000,None,None,[(0,3000)]),
                 ('clip3500',3500,None,1250,[(0,1250),(1251,3500)]),
                 ('gap4000',4000,1500,None,[(0,1500),(1501,4000)]),
                 ('restart_a',1500,None,None,[(0,1500)]),
                 ('restart_b',1500,None,None,[(0,1500)])]
    registry=ReaderSession()
    for name,n,gap,clip,expected_intervals in definitions:
        raw=synthetic(n,gap=gap,clip=clip)
        replay,packets=copy_slots(raw)
        rawfile=out/(name+'.bin');rawfile.write_bytes(replay)
        directory=out/name
        export(rawfile,directory,acquisition_id=name,config_version='framing-synthetic-1',
               source_kind='synthetic-code',provenance='B deterministic distinct lane codes',
               capture_point='offline two-slot copy replay, not hardware')
        record=registry.load(directory)
        actual_intervals=[(x['row_start'],x['row_stop']) for x in record.clean_intervals]
        assert actual_intervals==expected_intervals,(name,actual_intervals)
        case,data=inspect_record(record,raw,name)
        starts=[start+512*k for start,stop in expected_intervals
                for k in range(max(0,1+(stop-start-1024)//512))]
        assert [f['row_start'] for f in case['frames']]==starts
        case['packets']=packets
        case['partial_last_packet_is_logic_test_only']=bool(n%250)
        cases.append(case);arrays.update(data)
    raw=(S1/'raw.bin').read_bytes()
    replay,packets=copy_slots(raw)
    s1,unused=inspect_record(ReaderSession().load(S1),replay,'s1')
    assert len(s1['frames'])==561 and s1['summary']['unused_clean_rows']==506
    assert all(p['groups']==250 for p in packets) and len(packets)==1153
    assert s1['frames'][0]['packet_indices']==[0,1,2,3,4]
    assert s1['frames'][-1]['row_start']==286720
    s1['packet_count']=len(packets);cases.append(s1)
    rejects={}
    valid=synthetic(1500)
    mutations={'reserved':(28,1),'unknown_flag':(24,16),'bad_signed24':(8,8388608)}
    for name,(offset,value) in mutations.items():
        damaged=bytearray(valid);damaged[offset:offset+4]=int(value).to_bytes(4,'little')
        try:decode(bytes(damaged))
        except ValueError as exc:rejects[name]=str(exc)
        else:raise AssertionError('invalid input accepted: '+name)
    for name,damaged in [('truncated',valid[:-1]),('duplicate',valid[:32]+valid),
                         ('backwards',valid[32:64]+valid)]:
        try:decode(damaged)
        except ValueError as exc:rejects[name]=str(exc)
        else:raise AssertionError('invalid input accepted: '+name)
    result={'status':'AUTHOR_OFFLINE_FRAMING_GOLDEN_NOT_ADAPTER_ACCEPTANCE',
            'N':1024,'H':512,'packet_groups':250,'cases':cases,'rejections':rejects,
            'not_tested':['RTL/PS adapter','ready/valid stall','queue full','CDC','WCET','acoustics']}
    (out/'framing.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    np.savez_compressed(out/'synthetic-frames.npz',**arrays)
    spec=importlib.util.spec_from_file_location('upstream_budget',REPO/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/budget.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    (out/'budget.json').write_text(json.dumps(module.calculate(),indent=2)+'\n')
    return result

def compare(expected,actual):
    for filename in ['framing.json','budget.json']:
        if json.loads((Path(expected)/filename).read_text(encoding='utf-8')) != json.loads((Path(actual)/filename).read_text(encoding='utf-8')):
            raise ValueError('frozen mismatch: '+filename)
    with np.load(Path(expected)/'synthetic-frames.npz',allow_pickle=False) as a, np.load(Path(actual)/'synthetic-frames.npz',allow_pickle=False) as b:
        if set(a.files)!=set(b.files) or any(not np.array_equal(a[k],b[k]) for k in a.files):
            raise ValueError('frozen mismatch: PCM arrays')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=generate(a.out)
    print(json.dumps({'cases':len(r['cases']),'rejections':len(r['rejections']),'s1_frames':len(r['cases'][-1]['frames'])}))
