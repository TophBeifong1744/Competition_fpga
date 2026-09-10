"""Independent arithmetic audit; no author evidence is overwritten."""
import argparse
import hashlib
import json
import math
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('package', type=Path)
args = p.parse_args()
root = args.package.resolve()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
c = read(root/'contract.json')
old = read(root/'evidence/run01/evaluation.json')
new = read(root/'evidence/a-review-run01/evaluation.json')
differences = [k for k in old.keys() | new.keys() if old.get(k) != new.get(k)]
assert set(differences) <= {'environment'}, differences
manifest = read(root/'sources.json')
for path, record in manifest.items():
    assert sha(root/path) == record['sha256']
    original = root.parents[3]/record['source'].replace('\\', '/')
    # Original source paths are provenance only; the accepted bundle is self-contained.
    if original.exists():
        assert sha(original) == record['sha256']

totals = []
for candidate, reported in zip(c['candidates'], new['candidates'], strict=True):
    f = candidate['formats']
    sizes = [(6144,'pcm'), (6144,'pcm'), (6156,'fft_component'),
             (1026,'cross_component'), (1026,'phat_component'), (513,None),
             (1024,'correlation'), (15,'delay_samples'), (1024,'hann'),
             (48,'pcm'), (216,'audio_weight'), (1024,'pcm')]
    expected = [0,0,0]
    for count, kind in sizes:
        bits = f[kind]['W'] if kind else 1
        expected[0] += (count*bits+7)//8
        expected[1] += count*((bits+7)//8)
        expected[2] += count*(next(v for v in [8,16,32,64,128,256] if v >= bits)//8)
    assert expected == [reported['partial_totals'][key] for key in
                        ['bit_packed_bytes','byte_aligned_element_bytes','software_container_bytes']]
    assert f['cross_component']['W'] >= 2*f['fft_component']['W']+1
    assert f['cross_component']['F'] == 2*f['fft_component']['F']
    # 54 old-filter terms and 12 goal terms are accumulated separately, then blended.
    assert f['audio_accumulator']['W'] >= 24+24+math.ceil(math.log2(54))
    assert (2**17) < 2**f['hann']['W']
    assert (2**23) < 2**f['audio_weight']['W']
    totals.append(expected)

ops = new['operations_per_frame']
expected_ops = dict(rfft_real_1024=6, irfft_real_1024=15, hann_real_mult=6144,
    cross_complex_mult=15*513, cross_equivalent_real_mult=4*15*513,
    cross_equivalent_real_add=2*15*513, complex_magnitudes=15*513,
    complex_by_real_divisions=15*513,
    physical_lag_peak_candidates=12*(2*math.ceil(.04*48000/343)+1)
        +3*(2*math.ceil(math.sqrt(2)*.04*48000/343)+1))
assert ops == expected_ops
band = [k for k in range(513) if 300 <= k*48000/1024 <= 4000]
assert (len(band),band[0],band[-1]) == (79,7,85)
assert new['audio_operations']['filter_mac_upper_bound_per_second'] == 66*48000
assert new['selected_candidate'] is None
assert new['cycles_available_per_hop'] is None
assert new['confirmed_boundary']['h1']['normalization_denominator'] == 8388608
print(json.dumps(dict(status='PASS_DRAFT_ARITHMETIC_ONLY', semantic_differences=differences,
    evaluation_byte_identical=sha(root/'evidence/run01/evaluation.json')==sha(root/'evidence/a-review-run01/evaluation.json'),
    partial_totals=totals, band_bins=len(band), lag_candidates=ops['physical_lag_peak_candidates'],
    frame_rate=48000/512, equivalent_points_per_second=21*1024*48000/512,
    conservative_integer_cycles_at_100MHz=100000000*512//48000,
    limitation='Does not independently validate upstream audio algorithms or actual IP scheduling.'), indent=2))
