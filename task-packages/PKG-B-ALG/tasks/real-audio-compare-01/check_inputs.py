"""Step 2: bind accepted recordings; no format re-acceptance or audio rendering."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODEL = HERE.parents[1]/'payload/model/python'
sys.path.insert(0, str(MODEL))
from h1_reader import ReaderSession
from audio_frames import adapt_h1

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    config_path = HERE/'config.json'
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    manifest = ROOT/cfg['input_manifest']
    if sha(manifest) != cfg['input_manifest_sha256']:
        raise ValueError('HISTORICAL_MANIFEST_MISMATCH')
    hashes = json.loads(manifest.read_text(encoding='utf-8'))
    for name, expected in hashes.items():
        if sha(ROOT/name) != expected:
            raise ValueError('INPUT_HASH_MISMATCH: '+name)
    batch = ROOT/cfg['batch']
    out = args.out.resolve()
    if out.exists() or batch.resolve() in out.parents:
        raise ValueError('output must be new and outside frozen batch')
    reports = []
    session = ReaderSession()
    for name, role in zip(cfg['recordings'], cfg['roles'], strict=True):
        rec = session.load(batch/'delivery-01'/name)
        meta = rec.metadata
        for field, value in [('sample_rate_hz',cfg['sample_rate_hz']),
                             ('channel_order',cfg['channel_order']),
                             ('coordinates_m',cfg['positions_m'])]:
            if meta[field] != value:
                raise ValueError('CONFIGURATION_MISMATCH: '+field)
        segment = adapt_h1(rec)
        np.testing.assert_array_equal(segment.samples, rec.samples.astype(float)/cfg['pcm_divisor'])
        intervals = [dict(row_start=int(a), row_stop=int(b), sample_count=int(b-a),
                          first_sample_id=str(int(rec.sample_ids[a])),
                          last_sample_id=str(int(rec.sample_ids[b-1])))
                     for a,b in segment.clean_intervals]
        reports.append(dict(recording=name, role=role, rows=len(rec.samples),
            duration_s=len(rec.samples)/cfg['sample_rate_hz'],
            clean_intervals=intervals, excluded_error_rows=int(np.count_nonzero(rec.stream_error)),
            calibration_status=meta['calibration_status'],
            peak_abs_normalized=np.max(np.abs(segment.samples),axis=0).tolist(),
            reference_channel=cfg['reference_channel'],
            usable_for_input_binding=bool(intervals), acoustic_acceptance=False))
        if not intervals:
            raise ValueError('NO_CLEAN_INPUT_INTERVAL: '+name)
    for name, expected in hashes.items():
        if sha(ROOT/name) != expected:
            raise ValueError('INPUT_CHANGED_DURING_CHECK: '+name)
    result = dict(status='INPUT_BINDING_VERIFIED_ONLY',config_sha256=sha(config_path),
        historical_manifest_sha256=sha(manifest), inputs=hashes, recordings=reports,
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in
                 [Path(__file__), MODEL/'h1_reader.py', MODEL/'audio_frames.py']},
        environment=dict(python=platform.python_version(), numpy=np.__version__, platform=platform.platform()),
        audio_generated=False, manual_steering_is_ground_truth=False,
        note='Full clean intervals selected; output common crop and delay alignment will be defined in step3.')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as file:
        json.dump(result,file,ensure_ascii=False,indent=2,allow_nan=False)
        file.write('\n')
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))

if __name__ == '__main__':
    main()
