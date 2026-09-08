"""Unchanged numeric baseline excerpt; provenance in reference/six-mic-baseline/receipt.json."""
import numpy as np

FS, C, N, L = 48000, 343.0, 1024, 4096
BAND = (300, 4000)
START = 1536
SEED = 20260907
R = np.sqrt(2) * .020
POS = np.array([[-.020, -.020, 0], [.020, -.020, 0],
                [.020, .020, 0], [-.020, .020, 0], [0, 0, R], [0, 0, -R]])
PAIRS = [(i, j) for i in range(6) for j in range(i + 1, 6)]
B = np.array([POS[i] - POS[j] for i, j in PAIRS])
SCENARIOS = ["clean", "noise20", "noise10", "noise0", "band_noise0", "reflection",
             "interferer0", "mismatch", "one_channel_noise"]


def unit(az, el):
    a, e = np.deg2rad([az, el])
    return np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])


def angle(u, v):
    return float(np.rad2deg(np.arccos(np.clip(np.dot(u, v), -1, 1))))


def source(rng):
    f = np.fft.rfftfreq(L, 1 / FS)
    spec = np.fft.rfft(rng.normal(size=L))
    # Smooth spectral band edges; synthetic broadband probe, NOT natural speech.
    weight = np.clip((f - 200) / 200, 0, 1) * np.clip((4400 - f) / 600, 0, 1)
    x = np.fft.irfft(spec * weight, n=L)
    return x / np.std(x)


def shift(x, samples):
    """Periodic fractional shift; all reported samples come from an interior crop."""
    f = np.fft.rfftfreq(len(x))
    return np.fft.irfft(np.fft.rfft(x) * np.exp(-2j * np.pi * f * samples), n=len(x))


def render(x, u, distance=1.5, positions=POS, extra_delay=0):
    # Exact spherical path lengths; remove common distance/c (unknown emission time).
    d = np.linalg.norm(distance * u - positions, axis=1)
    delays = (d - distance) / C * FS + extra_delay
    return np.array([shift(x, t) * distance / di for t, di in zip(delays, d)])


def gcc(frame):
    x = np.fft.rfft(frame * np.hanning(N)[None, :], axis=1)
    f = np.fft.rfftfreq(N, 1 / FS)
    band = (f >= BAND[0]) & (f <= BAND[1])
    estimates = []
    for i, j in PAIRS:
        z = x[i] * x[j].conj()
        amp = np.abs(z)
        mask = band & (amp >= .02 * max(float(amp[band].max()), 1e-15))
        if mask.sum() < 12:
            estimates.append(np.nan)
            continue
        z = np.where(mask, z / np.maximum(amp, 1e-15), 0)
        corr = np.fft.irfft(z, n=N)
        bound = np.linalg.norm(POS[i] - POS[j]) / C * FS
        lim = int(np.ceil(bound))
        lags = np.arange(-lim, lim + 1)
        peak = int(lags[np.argmax(corr[lags % N])])
        ym, y0, yp = corr[(peak - 1) % N], corr[peak % N], corr[(peak + 1) % N]
        denom = ym - 2 * y0 + yp
        delta = np.clip(.5 * (ym - yp) / denom, -.5, .5) if denom < -1e-15 else 0.
        tau = peak + delta
        estimates.append(tau if abs(tau) <= bound + .05 else np.nan)
    return np.array(estimates)


def solve(tau):
    good = np.isfinite(tau)
    if good.sum() < 5 or np.linalg.matrix_rank(B[good]) < 3:
        return np.array([1., 0., 0.]), False, np.nan, np.nan
    # tau_ij = t_i - t_j; u points TO source, hence minus sign.
    raw = np.linalg.lstsq(B[good], -C / FS * tau[good], rcond=None)[0]
    norm = float(np.linalg.norm(raw))
    residual = float(np.sqrt(np.mean((B[good] @ raw * FS / C + tau[good]) ** 2)))
    valid = bool(.7 <= norm <= 1.3 and residual <= .5)
    return raw / max(norm, 1e-12), valid, residual, norm


def make_trial(az, el, repeat, scenario):
    # Same seeds across scenarios; mismatch is one fixed uncalibrated assembly.
    rng = np.random.default_rng(SEED + int(az) * 1000 + int(el + 90) * 10 + repeat)
    x, z = source(rng), source(rng)
    u = unit(az, el)
    actual = POS
    mrng = np.random.default_rng(SEED + 991)
    if scenario == "mismatch":
        actual = POS + mrng.uniform(-.0005, .0005, POS.shape)
    target = render(x, u, positions=actual)
    other = np.zeros_like(target)
    if scenario == "reflection":
        # Controlled two echoes, not a calibrated shoebox room or an RT60 model.
        target += .45 * render(x, unit(az + 110, -el / 2), positions=actual, extra_delay=FS * .003)
        target += .25 * render(x, unit(az - 75, 35), positions=actual, extra_delay=FS * .007)
    if scenario == "interferer0":
        other += render(z, unit(az + 90, 0), positions=actual)
    snr = {"clean": 120, "noise20": 20, "noise10": 10, "noise0": 0, "band_noise0": 120,
           "reflection": 20, "interferer0": 20, "mismatch": 20, "one_channel_noise": 20}[scenario]
    other += rng.normal(size=target.shape) * 10 ** (-snr / 20)
    if scenario == "band_noise0":
        other += np.array([source(rng) for _ in range(6)])
    if scenario == "one_channel_noise":
        # Channel 4 is noisy, not dropped. Baseline has no automatic channel detector.
        other[4] += rng.normal(size=L) * 10 ** (10 / 20)
    if scenario == "mismatch":
        gains = 10 ** (mrng.uniform(-1, 1, 6) / 20)
        ds = mrng.uniform(-.1, .1, 6)
        target = np.array([shift(t * g, d) for t, g, d in zip(target, gains, ds)])
        other = np.array([shift(t * g, d) for t, g, d in zip(other, gains, ds)])
    return u, target, other

