"""Audit B artifact consistency/aggregations, not rerun its PHAT/IFFT chain."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():
        raise SystemExit('Refusing to overwrite audit')
    sha=lambda b:hashlib.sha256(b).hexdigest()
    prov=json.loads((a.reference/'provenance.json').read_bytes())
    for f in prov['files']:
        assert sha((a.reference/f['local']).read_bytes()) == f['sha256'],f['local']
    packed=(a.reference/'evidence/run01/frames.json.gz').read_bytes()
    unpacked=gzip.decompress(packed)
    packing=json.loads((a.reference/'evidence/run01/packing.json').read_bytes())
    assert len(packed)==packing['compressed_bytes'] and sha(packed)==packing['compressed_sha256']
    assert len(unpacked)==packing['original_bytes'] and sha(unpacked)==packing['original_sha256']
    frames=json.loads(unpacked)
    analytic=json.loads((a.reference/'evidence/analytic01/checks.json').read_bytes())
    assert analytic['source_sha256']==sha((a.reference/'check_model.py').read_bytes())
    assert analytic['scan_sha256']==sha((a.reference/'scan.py').read_bytes())
    assert len(analytic['checks'])==12
    assert all(r['exact'] and not any(r['overflow']) for r in analytic['checks'])
    stats={}
    for candidate in ('reference25','shift6_late','shift6_early','wide29'):
        records=[]
        for exponent in (1,16,17,18,19,20,21,22,23,24):
            subset=[f for f in frames if f['peak_exponent']==exponent]
            valid=sum(p['valid'] for f in subset for p in f['candidates'][candidate]['pairs'])
            deltas=[abs(v['delta']) for f in subset for v in f['candidates'][candidate]['vs_float'] if v['delta'] is not None]
            changed=sum(v['peak_changed'] for f in subset for v in f['candidates'][candidate]['vs_float'])
            records.append({'exponent':exponent,'frames':len(subset),'valid_pairs':valid,
                            'max_tau_delta_vs_float':max(deltas) if deltas else None,
                            'integer_peak_changes':changed})
        stats[candidate]={'amplitudes':records,
                          'author_fft_overflow_frames':sum(any(f['candidates'][candidate]['flags']['fft_overflow']) for f in frames),
                          'author_fft_overflow_transforms':sum(sum(f['candidates'][candidate]['flags']['fft_overflow']) for f in frames)}
    out={'status':'PASS_ARCHIVE_INTEGRITY_AND_REAGGREGATION_ONLY',
         'B_commit':prov['source_commit'],'archived_files_verified':len(prov['files']),
         'npz_files_verified':len(prov['selected_cases']),
         'frames_json_decompressed_sha256':sha(unpacked),
         'analytic_author_records':12,'analytic_cmodel_reexecuted':False,
         'full_chain_reexecuted':False,'author_results_reaggregated':stats,
         'missing_from_git_but_in_b_manifest':prov['missing_from_git_but_in_b_manifest'],
         'stale_author_readme_head':'ac0ff38e954dac094fd84e28b329dcb24dded7fb; use B_commit above'}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'files':len(prov['files']),
                      'wide29_peak2^-20':stats['wide29']['amplitudes'][5],
                      'missing':out['missing_from_git_but_in_b_manifest']}))


if __name__=='__main__':
    main()
