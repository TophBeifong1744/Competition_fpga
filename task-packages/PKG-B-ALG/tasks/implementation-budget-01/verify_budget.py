"""Check saved accounting, quantization bounds and historical source integrity."""
import argparse,json,hashlib
from pathlib import Path
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main(out):
    root=Path(__file__).resolve().parents[2];ledger=read(out/'ledger.json');run=read(out/'run.json')
    assert (ledger['channels'],ledger['pairs'],ledger['frame'],ledger['hop'],ledger['band_bins'])==(6,15,1024,512,79)
    assert ledger['frames_per_second']==48000/512
    for k,table in ledger['buffer_inventory_bytes'].items():assert sum(table.values())==ledger['inventory_totals_bytes'][k]
    observations=read(out/'observations.json');frames=0
    for r in observations:
        n=r['frames'];frames+=n;calls=r['calls']
        assert calls['rfft_vectors']==6*n and calls['irfft_vectors']<=15*n
        assert r['retained_frame_payload_bytes']==n*6*1024*8
    quant=read(out/'quantization-risk.json')
    for q in quant['delay_only']:
        assert q['frames']==frames and q['max_delay_error_samples']<=.5/(2**q['delay_fraction_bits'])+1e-14
    for q in quant['coefficient_only']:
        assert q['max_output_error_bound_for_abs_input_le1']<=q['universal_54_tap_rounding_bound']+1e-14
    for path,h in run['unchanged_files'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==h,path
    for path,h in run['artifacts'].items():assert hashlib.sha256((out/path).read_bytes()).hexdigest()==h,path
    print('PASS: exact counts, inventory sums, observed FFT upper bounds, quantization bounds, source/evidence hashes; frames',frames)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);main(p.parse_args().out.resolve())
