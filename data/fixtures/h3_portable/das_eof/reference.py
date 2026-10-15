"""Contract-derived finite DAS expectations. Never imports the DUT.

Model card and qualified claims are in README.md. All coordinates here are
local emit coordinates; the schedule/audit checker adds the absolute origin.
"""
from fractions import Fraction

Q = 4096
ZERO_DELAYS = (0, 22928, 22928, 0)  # accepted six-angle literal, angle 0
FRESH_EMITS = (2562, 3074, 3586, 4098)


def ties_even(numerator, denominator):
    # Fraction.__round__ is exact, including negative ties; no DUT helper.
    return round(Fraction(int(numerator), int(denominator)))


def beam(pcm, n, delays=ZERO_DELAYS):
    if n < 0:
        return 0
    width = len(pcm[0])
    total = Fraction(0)
    for ch, delay in enumerate(delays):
        position = Fraction(n) - Fraction(delay, Q)
        left = position.numerator // position.denominator
        fraction = position - left
        a = int(pcm[ch][left]) if 0 <= left < width else 0
        b = int(pcm[ch][left + 1]) if 0 <= left + 1 < width else 0
        total += a * (1 - fraction) + b * fraction
    return round(total / 4)


def lanes(pcm, *, long=False, stop=None, fatal=None):
    """Bounded fixture model, not a generic tracker or serialized DAS clone.

    Known fixture locks at 2562 and repeats the same accepted angle 0. The
    480-point fade ends before every subsequent take. STOP either arrives after
    the fade has ended (3100/4098/E-1) or at EOF (no renderer control).
    """
    width = len(pcm[0])
    size = width + 8 if fatal is None else min(width + 8, fatal)
    manual = [beam(pcm, n) for n in range(width)]
    raw = []
    for emit in range(size):
        n = emit - 8
        mono = int(pcm[0][n]) if 0 <= n < width else 0
        if not long or emit < FRESH_EMITS[0]:
            value = mono
        else:
            angled = beam(pcm, n)
            if emit < FRESH_EMITS[0] + 480:
                alpha = ties_even((emit - FRESH_EMITS[0]) * Q, 480)
                value = ties_even(mono * (Q - alpha) + angled * alpha, Q)
            elif stop is not None and stop < width + 8 and emit >= stop:
                alpha = min(Q, ties_even((emit - stop) * Q, 480))
                value = ties_even(angled * (Q - alpha) + mono * alpha, Q)
            else:
                value = angled
        raw.append(value)
    count = min(width, max(0, size - 8))
    return {"single": list(map(int, pcm[0][:count])), "manual": manual[:count],
            "automatic": raw[8:8 + count], "automatic_raw": raw}


def expected_units():
    # B r2 dual-domain 53 required instances, frozen public identity contract.
    units = ["transport", "frame_domain", "binding"]
    for ch in range(4):
        units += [f"mean_{ch}", f"gate_window_{ch}", f"doa_window_{ch}"]
    for domain in ("gate", "doa"):
        for ch in range(4):
            units += [f"{domain}_fft_{ch}", f"{domain}_fixed4_{ch}"]
    units += ["gate_state"]
    for pair in ("01", "02", "03", "12", "13", "23"):
        units += [f"phat_{pair}", f"ifft_{pair}", f"lag_{pair}"]
    return units + ["doa", "tracker", "result_binding"]


def schedule(first, *, long, stop=None, fatal=None):
    count = 7 if long else 1
    rows = []
    for frame in range(count):
        last = first + 1023 + frame * 512
        available = last + (1 if long else 0)
        external = ["transport", "frame_domain", "binding"]
        external += [f"{domain}_{node}_{ch}" for domain in ("gate", "doa")
                     for ch in range(4) for node in ("fft", "fixed4")]
        if long and frame >= 2:
            external += ["ifft_" + pair for pair in ("01", "02", "03", "12", "13", "23")]
        rows.append({"frame_index": frame, "external_visible_at": {k: available for k in external},
                     "external_error_units": [], "available": available,
                     "commit_now": available + 1, "take_now": available + 2,
                     "audio_valid_through_emit": available + 1024 if long else None})
    value = {"time_basis": "SYNTHETIC_TIME", "boot_id": "DAS_EOF_B_BOOT",
             "session_id": "DAS_EOF_B_SESSION", "interval_id": "DAS_EOF_B_INTERVAL",
             "generation": 23, "first_sample_id": first,
             "result_ttl_samples": 1000 if long else 4, "frames": rows}
    if stop is not None:
        value["stop_emit"] = first + stop
    if fatal is not None:
        value["fatal_emit"] = first + fatal
    return value
