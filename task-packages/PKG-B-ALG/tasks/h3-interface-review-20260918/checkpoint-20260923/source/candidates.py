"""Small explicitly experimental set, no production defaults changed."""
import numpy as np

def features(pcm, lo=7, hi=72):
    raw = np.asarray(pcm)
    if raw.shape != (1024, 4) or not np.issubdtype(raw.dtype, np.integer):
        raise ValueError('1024x4 integer PCM required')
    if np.any(raw < -2**23) or np.any(raw >= 2**23):
        raise ValueError('signed24 required')
    x = raw.astype(np.float64)
    centered = x-x.mean(axis=0)
    window = np.hanning(len(x))
    spectrum = np.fft.rfft(centered*window[:, None], axis=0)
    # Parseval: rectangular-band contribution to window-normalized code^2 power.
    band_power = 2*np.sum(np.abs(spectrum[lo:hi+1])**2, axis=0)/(len(x)*np.sum(window**2))
    return dict(raw_rms=np.sqrt(np.mean(x*x, axis=0)).tolist(),
                centered_rms=np.sqrt(np.mean(centered**2, axis=0)).tolist(),
                peak=np.max(np.abs(x), axis=0).tolist(), band_power=band_power.tolist(),
                endpoint=bool(np.any((raw == -2**23) | (raw == 2**23-1))))

class BandActivity:
    """Background-calibrated, not online-learning, not a speech/identity detector."""
    def __init__(self, noise, cfg):
        self.noise = np.maximum(np.asarray(noise, dtype=float), cfg['band_rms_floor_codes']**2)
        if self.noise.shape != (4,) or not np.isfinite(self.noise).all():
            raise ValueError('finite four-channel background power required')
        self.cfg = cfg
        self.reset()

    def reset(self):
        self.active = False
        self.attack = self.release = 0

    def update(self, power, invalid=False):
        p = np.asarray(power, dtype=float)
        if p.shape != (4,) or not np.isfinite(p).all() or np.any(p < 0):
            raise ValueError('finite nonnegative four-channel power required')
        if invalid:
            self.reset()
            return False
        on = np.count_nonzero(p >= self.cfg['on_power_ratio']*self.noise) >= self.cfg['minimum_active_channels']
        off = np.count_nonzero(p >= self.cfg['off_power_ratio']*self.noise) < self.cfg['minimum_active_channels']
        self.attack = self.attack+1 if on else 0
        self.release = self.release+1 if off else 0
        if not self.active and self.attack >= self.cfg['attack_frames']:
            self.active = True
            self.release = 0
        elif self.active and self.release >= self.cfg['release_frames']:
            self.active = False
            self.attack = 0
        return self.active

def decisions(feature, gate, cfg):
    invalid = feature['endpoint']
    enough = cfg['minimum_active_channels']
    return dict(
        dc_only=bool(not invalid and np.count_nonzero(np.asarray(feature['centered_rms']) >= 2048) >= enough),
        band_absolute=bool(not invalid and np.count_nonzero(np.asarray(feature['band_power']) >= cfg['band_rms_floor_codes']**2) >= enough),
        band_calibrated_duration=gate.update(feature['band_power'], invalid))

def wrapped_error(angle, nominal):
    return abs((float(angle)-float(nominal)+180) % 360-180)

def direction_summary(rows, nominal, key, threshold=15):
    angles = [r[key] for r in rows if r[key] is not None]
    errors = [wrapped_error(v, nominal) for v in angles] if nominal is not None else []
    wrong = sum(v > threshold for v in errors)
    return dict(eligible_frames=len(rows), output_frames=len(angles), rejected_frames=len(rows)-len(angles),
        output_fraction=len(angles)/len(rows) if rows else None,
        nominal_deviation_p50_deg=float(np.percentile(errors, 50)) if errors else None,
        nominal_deviation_p95_deg=float(np.percentile(errors, 95)) if errors else None,
        nominal_gt15_count=wrong if nominal is not None else None,
        nominal_gt15_over_outputs=wrong/len(errors) if errors else None,
        nominal_gt15_over_eligible=wrong/len(rows) if rows and nominal is not None else None,
        formal_accuracy_accepted=False)
