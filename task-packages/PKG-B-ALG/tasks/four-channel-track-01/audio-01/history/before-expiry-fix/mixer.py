"""Offline causal-index DAS bank and finite convex crossfades.

No signal normalization, VAD, localization or tracking thresholds live here.
Input is an ordered list of already available diagnostic direction events.
"""
import math
import numpy as np


class Crossfade:
    def __init__(self, size, fade_samples=480):
        if type(size) is not int or size < 1 or type(fade_samples) is not int or fade_samples < 1:
            raise ValueError('positive integer size and fade length required')
        self.fade = fade_samples
        self.initial = np.zeros(size)
        self.initial[0] = 1.
        self.target = 0
        self.start = 0
        self.expiries = np.full(size, -np.inf)

    def weights(self, n):
        alpha = min(1., max(0., (n-self.start)/self.fade))
        w = self.initial*(1-alpha)
        w[self.target] += alpha
        # Each direction owns its original lifetime. A new direction cannot
        # prolong a different old beam still present in a crossfade.
        guard = np.clip((self.expiries[1:]+1-n)/self.fade, 0., 1.)
        removed = w[1:]*(1-guard)
        w[1:] *= guard
        w[0] += float(removed.sum())
        return w

    def select(self, target, n, valid_through=None):
        if type(target) is not int or not 0 <= target < len(self.initial):
            raise ValueError('invalid bank target')
        if target and (valid_through is None or not math.isfinite(valid_through) or valid_through < n):
            raise ValueError('beam requires unexpired validity')
        current = self.weights(n)
        if target:
            self.expiries[target] = valid_through
        self.initial = current
        self.target = target
        self.start = n


def mix_timeline(bank, start, stop, events, fade_samples):
    """events: ready reference index, target bank index, inclusive expiry.

    State must be reset per clean interval. Expiry is enforced at every sample,
    including after the last event. Decisions are applied to reference n only
    when ready <= n; fixed DAS audio availability is accounted for separately.
    """
    signals = np.asarray(bank, dtype=float)
    if signals.ndim != 2 or signals.shape[1] != stop-start or stop <= start or not np.isfinite(signals).all():
        raise ValueError('finite bank x common-crop signals required')
    if any(events[i]['ready'] >= events[i+1]['ready'] for i in range(len(events)-1)):
        raise ValueError('strictly ordered events required')
    for event in events:
        if type(event['ready']) is not int or event['ready'] < 0:
            raise ValueError('nonnegative integer ready sample required')
        if type(event['target']) is not int or not 0 <= event['target'] < len(signals):
            raise ValueError('invalid target')
    mixer = Crossfade(len(signals), fade_samples)
    weights = np.zeros((stop-start, len(signals)))
    targets = np.zeros(stop-start, dtype=np.int32)
    position = 0
    for n in range(start, stop):
        while position < len(events) and events[position]['ready'] <= n:
            event = events[position]
            # Replay earlier events at their own time, not at the cropped start.
            if event['fresh'] or event['target'] != mixer.target:
                mixer.select(event['target'], event['ready'], event['valid_through'])
            position += 1
        weights[n-start] = mixer.weights(n)
        targets[n-start] = mixer.target
    if np.any(weights < -1e-14) or not np.allclose(weights.sum(axis=1), 1, rtol=0, atol=1e-14):
        raise RuntimeError('NONCONVEX_MIX')
    output = np.sum(signals.T*weights, axis=1)
    return output, weights, targets
