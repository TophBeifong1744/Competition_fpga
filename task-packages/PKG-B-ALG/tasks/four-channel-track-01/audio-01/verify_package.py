"""Check this explicit audio revision plus the unchanged parent snapshot."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_three import HERE,PARENT,ROOT,load,sha,verify_inputs,comparison


def verify():
    pins=verify_inputs()
    manifest=load(HERE/'MANIFEST.json')
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    if actual!=set(manifest)|{'MANIFEST.json'}: raise ValueError('AUDIO_FILE_SET_CHANGED')
    for p,want in manifest.items():
        if sha(HERE/p)!=want: raise ValueError('AUDIO_FILE_CHANGED: '+p)
    parent_files={p.relative_to(PARENT).as_posix() for p in PARENT.rglob('*')
                  if p.is_file() and HERE not in p.parents}
    if parent_files!=set(load(PARENT/'MANIFEST.json'))|{'MANIFEST.json'}:
        raise ValueError('UNDECLARED_PARENT_ADDITION')
    tested=load(HERE/'evidence/run02/audio/result.json')['source_sha256']
    for p,want in tested.items():
        if sha(ROOT/p)!=want: raise ValueError('TESTED_SOURCE_CHANGED: '+p)
    for run in ('run01','run02'):
        directory=HERE/'evidence'/run/'audio'
        for p,want in load(directory/'SHA256.json').items():
            if sha(directory/p)!=want: raise ValueError('HISTORICAL_OUTPUT_CHANGED: '+run+'/'+p)
    old=load(HERE/'evidence/run01/audio/result.json')['source_sha256']
    for p,want in old.items():
        path=ROOT/p
        if path.name in ('mixer.py','test_audio.py'):
            path=HERE/'history/before-expiry-fix'/path.name
        if sha(path)!=want: raise ValueError('HISTORICAL_SOURCE_CHANGED: '+p)
    listening=load(HERE/'evidence/listening-01.json')
    if len(listening['presented_files'])!=3: raise ValueError('LISTENING_FILE_SET_CHANGED')
    for p,want in listening['presented_files'].items():
        if sha(HERE/p)!=want: raise ValueError('LISTENING_AUDIO_CHANGED: '+p)
    if sha(HERE/'evidence/run02/audio/result.json')!=listening['render_result_sha256']:
        raise ValueError('LISTENING_RENDER_CHANGED')
    return dict(status='PACKAGE_AND_SOURCE_BINDINGS_PASS',revision_files=len(manifest),
                parent_files=len(parent_files),pinned_inputs_and_dependencies=len(pins),
                tested_sources=len(tested),historical_sources_bound=True,
                listening_files_bound=3,
                scope='author integrity check; B subjective feedback recorded; A review pending')


def compare_saved():
    a=HERE/'evidence/run01/audio';b=HERE/'evidence/run02/audio'
    x,y=load(a/'result.json'),load(b/'result.json')
    stats=dict(float_values=0,discrete_values=0,max_abs_error=0.)
    for key in ('config','input_pins','records','environment','limits'):
        comparison.compare_values(x[key],y[key],key,stats)
    details=[]
    for path in sorted(a.glob('*.wav')):
        details.append(dict(file=path.name,bytes_equal=sha(path)==sha(b/path.name)))
    arrays=[]
    for path in sorted(a.glob('*.npz')):
        with np.load(path,allow_pickle=False) as left,np.load(b/path.name,allow_pickle=False) as right:
            if left.files!=right.files: raise ValueError('NPZ_KEYS_CHANGED')
            for key in left.files:
                if not np.array_equal(left[key],right[key]): raise ValueError('MIX_ARRAY_CHANGED')
            arrays.append(dict(file=path.name,arrays_exact=True,bytes_equal=sha(path)==sha(b/path.name)))
    if not all(r['bytes_equal'] for r in details): raise ValueError('WAV_BYTES_CHANGED')
    return dict(status='SAVED_RECORDINGS_UNCHANGED_BY_EXPIRY_FIX',values=stats,wav_files=details,mix_files=arrays,
        result_json_bytes_equal=sha(a/'result.json')==sha(b/'result.json'),
        changed_source_paths=[p for p,h in x['source_sha256'].items() if y['source_sha256'].get(p)!=h],
        interpretation='These short real captures do not exercise expiry retargeting. The two added regression tests do; preserved failure is not erased.')


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--compare-saved',action='store_true')
    args=ap.parse_args()
    print(json.dumps(compare_saved() if args.compare_saved else verify(),ensure_ascii=False,indent=2))
