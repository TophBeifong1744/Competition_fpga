"""Integer composition reference from the frozen mathematical contract.

No import from soundsight_h3_portable or historic leaf implementations. ROM
bytes are shared numeric inputs and explicitly bound, so this is independent
arithmetic and wiring evidence, not an independent ROM-generation oracle.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


PAIRS = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rne(value, denominator):
    assert denominator > 0
    q, remainder = divmod(abs(int(value)), denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and q % 2):
        q += 1
    return -q if value < 0 else q


def signed_limit(value, width):
    low, high = -(1 << (width - 1)), (1 << (width - 1)) - 1
    return min(high, max(low, value)), not low <= value <= high


def fixed4_complex(re, im):
    qr, bad_r = signed_limit(rne(re, 16), 25)
    qi, bad_i = signed_limit(rne(im, 16), 25)
    return ((0, 0) if (bad_r or bad_i) else (qr, qi)), (bad_r, bad_i)


def recursive_fft(values, twiddles, width):
    """Even/odd recursion, distinct from the DUT's bit-reversed in-place loop."""
    if len(values) == 1:
        return values
    even = recursive_fft(values[::2], twiddles, width)
    odd = recursive_fft(values[1::2], twiddles, width)
    half = len(values) // 2
    stage = twiddles[half - 1:2 * half - 1]
    answer = [None] * len(values)
    for k in range(half):
        wr, wi = map(int, stage[k])
        br, bi = odd[k]
        tr = rne(wr * br - wi * bi, 1 << 30)
        ti = rne(wr * bi + wi * br, 1 << 30)
        ar, ai = even[k]
        for index, raw in ((k, (ar + tr, ai + ti)),
                           (k + half, (ar - tr, ai - ti))):
            re, over_re = signed_limit(rne(raw[0], 2), width)
            im, over_im = signed_limit(rne(raw[1], 2), width)
            if over_re or over_im:
                raise ArithmeticError("independent FFT overflow at stage size " + str(len(values)))
            answer[index] = (re, im)
    return answer


def table_check(table):
    failures = []
    checks = 0
    for inverse in (False, True):
        cursor = 0
        for size in (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024):
            for j in range(size // 2):
                angle = (1 if inverse else -1) * 2.0 * math.pi * j / size
                expected = (round(math.cos(angle) * (1 << 30)),
                            round(math.sin(angle) * (1 << 30)))
                actual = tuple(map(int, table[int(inverse), cursor + j]))
                checks += 1
                if actual != expected:
                    failures.append((inverse, size, j, expected, actual))
            cursor += size // 2
    return checks, failures


def cross_and_mask(halves):
    crosses = np.zeros((6, 513, 2), dtype=np.int64)
    masks = np.zeros((6, 513), dtype=np.uint8)
    for p, (left, right) in enumerate(PAIRS):
        for bin_index in range(513):
            ar, ai = map(int, halves[left, bin_index])
            br, bi = map(int, halves[right, bin_index])
            crosses[p, bin_index] = (ar * br + ai * bi,
                                     ai * br - ar * bi)
        band_squares = [int(crosses[p, k, 0]) ** 2 + int(crosses[p, k, 1]) ** 2
                        for k in range(7, 86)]
        maximum = max(band_squares)
        for k, square in enumerate(band_squares, start=7):
            masks[p, k] = int(square > 0 and 2500 * square >= maximum)
    return crosses, masks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    a.out.mkdir()
    package = a.repo / "models/python/soundsight_h3_portable"
    manifest = json.loads((package / "tables/source-manifest.json").read_text())
    hann_row = manifest["entries"]["hann"]
    hann_path = a.repo / hann_row["path"]
    assert sha(hann_path) == hann_row["sha256"]
    hann = np.frombuffer(hann_path.read_bytes(), dtype="<u4").astype(np.int64)
    assert hann.shape == (1024,)
    table_path = package / "tables/fft-q30-i32le.bin"
    atan_path = package / "tables/cordic-atan-q16-i32le.bin"
    table_spec = json.loads((package / "tables/table-manifest.json").read_text())
    assert sha(table_path) == table_spec["fft"]["sha256"]
    assert sha(atan_path) == table_spec["atan"]["sha256"]
    twiddle = np.frombuffer(table_path.read_bytes(), dtype="<i4").reshape(2, 1023, 2)
    atan = np.frombuffer(atan_path.read_bytes(), dtype="<i4")
    count, failures = table_check(twiddle)
    assert not failures, failures[:1]
    assert len(atan) == 24
    assert all(int(v) == round(math.degrees(math.atan(2.0 ** -i)) * (1 << 16))
               for i, v in enumerate(atan))
    pcm = np.load(a.fixture / "pcm.npy", allow_pickle=False)
    assert pcm.shape == (4, 4096)
    arrays = {}
    denom = sum(int(w) ** 2 for w in hann)
    for frame in range(7):
        x = pcm[:, frame * 512:frame * 512 + 1024]
        means = np.asarray([rne(sum(map(int, x[ch])), 1024) for ch in range(4)], dtype=np.int64)
        centered = x - means[:, None]
        gate = np.asarray([[rne(int(centered[ch, n]) * int(hann[n]), 1 << 17)
                            for n in range(1024)] for ch in range(4)], dtype=np.int64)
        doa = np.asarray([[rne(int(x[ch, n]) * int(hann[n]), 1 << 17)
                           for n in range(1024)] for ch in range(4)], dtype=np.int64)
        for name, values in (("mean_s24", means), ("gate_centered_s25", centered),
                             ("gate_window_s25", gate), ("doa_window_s24", doa)):
            arrays[f"frame{frame:04d}_{name}"] = values
        halves = {}
        for domain, window in (("gate", gate), ("doa", doa)):
            full = np.asarray([recursive_fft([(int(v) << 4, 0) for v in window[ch]],
                                             twiddle[0], 29) for ch in range(4)], dtype=np.int64)
            half = np.empty((4, 513, 2), dtype=np.int64)
            for ch in range(4):
                for bin_index in range(513):
                    values, overflow = fixed4_complex(*map(int, full[ch, bin_index]))
                    assert not any(overflow), (frame, domain, ch, bin_index)
                    half[ch, bin_index] = values
            arrays[f"frame{frame:04d}_{domain}_fft29"] = full
            arrays[f"frame{frame:04d}_{domain}_half25"] = half
            halves[domain] = half
        powers = []
        for ch in range(4):
            total = sum(int(re) ** 2 + int(im) ** 2 for re, im in halves["gate"][ch, 7:73])
            powers.append(rne(2 * total * 1024 * (1 << 34), denom))
        arrays[f"frame{frame:04d}_gate_band_power_u64"] = np.asarray(powers, dtype=np.uint64)
        crosses, masks = cross_and_mask(halves["doa"])
        if frame < 2:
            crosses[:] = 0
            masks[:] = 0
        arrays[f"frame{frame:04d}_phat_cross_s51"] = crosses
        arrays[f"frame{frame:04d}_phat_mask"] = masks
    np.savez_compressed(a.out / "expected-stages.npz", **arrays)
    boundary = {
        "positive_half_to_even": rne(8, 16), "negative_half_to_even": rne(-8, 16),
        "positive_three_halves": rne(24, 16), "negative_three_halves": rne(-24, 16),
        "positive_max_s29": fixed4_complex((1 << 28) - 1, 0),
        "negative_min_s29": fixed4_complex(-(1 << 28), 0),
    }
    assert boundary["positive_max_s29"] == ((0, 0), (True, False))
    assert boundary["negative_min_s29"] == ((-(1 << 24), 0), (False, False))
    (a.out / "reference-summary.json").write_text(json.dumps({
        "independence": "no DUT/leaf import; shared frozen ROM bytes are bound inputs",
        "table_values_checked": count, "atan_values_checked": len(atan),
        "boundary": boundary,
        "array_count": len(arrays),
        "expected_sha256": sha(a.out / "expected-stages.npz"),
    }, indent=2) + "\n", encoding="utf-8")
    print((a.out / "reference-summary.json").read_text())


if __name__ == "__main__":
    main()
