def front(pcm):
    x = np.asarray(pcm)
    if x.shape != (1024, 4) or not np.issubdtype(x.dtype, np.integer) or np.any(x < -2 ** 23) or np.any(x >= 2 ** 23):
        raise ValueError('signed24 1024x4 required')
    x = x.astype(np.int64)
    means = np.array([fixed.rne_div(sum(map(int, x[:, ch])), 1024) for ch in range(4)], dtype=np.int64)
    centered = x - means
    window = fixed.hann_u18f17()
    weighted = np.array([[fixed.rne_shift(int(v) * int(w), 17) for v, w in zip(centered[:, ch], window)] for ch in range(4)], dtype=np.int64)
    return (x, means, centered, window, weighted)

def power(half, window):
    denominator = sum((int(w) ** 2 for w in window))
    sums = [sum((int(a) ** 2 + int(b) ** 2 for a, b in half[ch, 7:73])) for ch in range(4)]
    numerators = [2 * s * 1024 * (1 << 34) for s in sums]
    powers = [fixed.rne_div(n, denominator) for n in numerators]
    assert all((0 <= n < 2 ** 104 for n in numerators)) and all((0 <= p < 2 ** 64 for p in powers))
    return (sums, numerators, denominator, powers)
