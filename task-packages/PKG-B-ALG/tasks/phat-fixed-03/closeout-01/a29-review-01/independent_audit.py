"""B checks Git provenance, decompressed bytes, job mapping and timing independently."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

A_SHA='c0b5f8fb44643e81d8c4e6f0be457dddeae9758e'
B_SHA='bff45e7bbedab321fc4815e1432f1575c750edc4'

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--a-root',type=Path,required=True)
    ap.add_argument('--vectors',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); assert not a.out.exists()
    git=['git','-c',f'safe.directory={a.a_root.as_posix()}','-C',str(a.a_root)]
    assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==A_SHA
    pkg=a.a_root/'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01'
    ref=pkg/'reference/b-dynamic-range'
    prov=json.loads((ref/'provenance.json').read_bytes())
    checks=[]
    for r in prov['files']:
        blob=subprocess.check_output(git+['show',f'{B_SHA}:{r["source"]}'])
        stored=(ref/r['local']).read_bytes()
        assert stored==blob and sha(blob)==r['sha256']
        assert hashlib.sha1(f'blob {len(blob)}\0'.encode()+blob).hexdigest()==r['git_blob']
        checks.append(dict(source=r['source'],sha256=sha(blob),git_blob=r['git_blob']))
    for name in ['build.tcl','simulate.tcl','tb_fft.sv','contract.json']:
        original=subprocess.check_output(git+['show',f'ac0ff38e954dac094fd84e28b329dcb24dded7fb:task-packages/PKG-A-ACQ/tasks/fft-ip-budget-01/{name}'])
        assert original==(pkg/'reference/a25-ac0ff38'/name).read_bytes()
    sim=pkg/'evidence/run01/simulation'
    for r in json.loads((sim/'packing.json').read_bytes()):
        stored=(sim/r['stored_name']).read_bytes()
        assert sha(stored)==r['stored_sha256']
        raw=gzip.decompress(stored) if r['stored_name'].endswith('.gz') else stored
        assert len(raw)==r['original_bytes'] and sha(raw)==r['original_sha256']
    frames=json.loads(gzip.decompress((ref/'evidence/run01/frames.json.gz').read_bytes()))
    ids=[r['case'] for r in frames if r['peak_exponent'] in [1,16,17,18,20,21,24] or r['case']>=192]
    assert len(ids)==60 and ids==prov['selected_cases']
    assert set(prov['unselected_cases'])==set(range(196))-set(ids)
    selected=json.loads((a.vectors/'selection.json').read_bytes())
    expected=np.load(a.vectors/'expected.npy',allow_pickle=False)
    stream=np.array([int(x,16) for x in (a.vectors/'inputs.mem').read_text().split()],dtype=np.uint64).reshape(361,1024)
    output=np.loadtxt(gzip.open(sim/'outputs.csv.gz','rt'),delimiter=',',dtype=np.int64).reshape(361,1024,4)
    np.testing.assert_array_equal(output[:,:,0],np.repeat(np.arange(361)[:,None],1024,axis=1))
    np.testing.assert_array_equal(output[:,:,1],np.tile(np.arange(1024),(361,1)))
    for job in range(361):
        case,channel=(ids[job//6],job%6) if job<360 else (0,0)
        j=selected['jobs'][job]
        assert j['case']==case and j['channel']==channel and j['backpressure']==(job==360)
        with np.load(ref/f'evidence/run01/case-{case:03d}.npz',allow_pickle=False) as z:
            np.testing.assert_array_equal(stream[job],(z['windowed'][channel]*16)&((1<<29)-1))
            np.testing.assert_array_equal(expected[job],z['wide29_raw_fft'][channel])
            np.testing.assert_array_equal(output[job,:,2:],z['wide29_raw_fft'][channel])
    vectors={}
    for name in ['inputs.mem','expected.npy','job-count.mem','selection.json']:
        current=(a.vectors/name).read_bytes(); old=(pkg/'evidence/run01/vectors'/name).read_bytes()
        assert current==old, name
        vectors[name]=sha(current)
    c=np.loadtxt(gzip.open(sim/'cycles.csv.gz','rt'),delimiter=',',dtype=np.int64)
    status=np.loadtxt(gzip.open(sim/'status.csv.gz','rt'),delimiter=',',dtype=np.int64)
    assert c.shape==(361,6) and status.shape==(361,3)
    np.testing.assert_array_equal(c[:,0],np.arange(361))
    np.testing.assert_array_equal(status[:,0],np.arange(361))
    assert np.all(status[:,2]==0)
    assert np.all(np.diff(c[:,1:],axis=1)>=0)
    assert np.all(c[:-1,5]-c[:-1,1]==7361)
    assert np.all(np.diff(c[:-1,1])==7366)
    assert c[5,5]-c[0,1]==44191 and c[-1,5]-c[-1,1]==7599
    result=dict(status='B_INDEPENDENT_ARCHIVE_AND_INPUT_AUDIT_ONLY',A_commit=A_SHA,B_commit=B_SHA,
        original_B_git_files=checks,A25_files_git_equal=4,simulation_packing_records_verified=11,
        vectors_regenerated_bytes_equal=vectors,selected_frames=60,unselected_frames=136,
        transforms=361,integer_codes_compared=739328,mismatches=0,overflow=0,
        normal_cycles=7361,service_slot_cycles=7366,six_fft_cycles=44191,six_slots_cycles=44196,
        backpressure_cycles=7599,new_RTL_executed_by_this_script=False)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('B independent Git/packing/job-map/timing audit PASS; no new RTL in this command')

if __name__=='__main__': main()
