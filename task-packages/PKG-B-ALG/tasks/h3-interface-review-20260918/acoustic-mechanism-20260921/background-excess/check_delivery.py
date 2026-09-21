"""Replay archived controls without repeating FFT study."""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    j=load(a.input/'result.json');rows=load(a.input/'frames.json')
    assert sha(a.input/'pre-noise-p95.npy')==j['reference_sha256']
    assert sha(Path(__file__).with_name('probe.py'))==j['source_sha256']
    for n,h in {**j['pins'],**j['dependencies']}.items():assert sha(a.repo/n)==h,n
    path=a.repo/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py';s=importlib.util.spec_from_file_location('excess_replay',path);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
    for capture in j['captures']:
        selected=[r for r in rows if r['capture']==capture['capture']];t=m.Tracker(m.Config(cone_half_angle_deg=60))
        assert len(selected)==capture['groups']['whole_recording']['frames']
        for r in selected:
            if not r['gate']:t.reset()
            angle=r['new_angle'];v=None if angle is None else [math.cos(math.radians(angle)),math.sin(math.radians(angle)),0]
            assert t.update(r['stop']/48,v,r['gate'] and r['new_valid'])==r['tracker']
    result=dict(replayed_states=len(rows),input_files_verified=len({**j['pins'],**j['dependencies']}),reference_sha256=j['reference_sha256'],new_fft_calls=0,status='ARCHIVE_AND_CONTROL_REPLAY_PASS')
    (a.out/'result.json').write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':main()
