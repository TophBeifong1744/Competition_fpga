# B independent marker and candidate activity review

Audited SHA: `94b5fe79d87e038e895878fb31030cded469bb33`.

Read PUBLICATION.md then HANDOFF-20260920.md, playback-v1/timeline.json, scripts/process_capture.py and six archived alignment.json files. Selected raw data only through the 72-entry CURRENT-DATA-SHA256.json, excluding historical received-20260920-01.

Executed command (exit 0):

```powershell
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B F:/NUEC/review-evidence/eight-94b5fe7/markers/check_markers.py
```

Independent code reads signed int32 PCM directly from raw BIN word columns 2..5. It uses FFT cross-correlation with conjugated template FFT (rather than importing the author's reversed-template implementation), local mean/energy normalization, and verifies each selected peak with a direct time-domain dot product. Both marker WAVs exactly equal the corresponding source-WAV samples. All 48 peaks and normalized correlations match archived results within 1e-8. No rewriting, gain change or channel shift is applied to raw data.

The source contains a 0.15 s start chirp at 0.2 s and a 0.15 s end chirp at 4.45 s; the speech source occupies 1.0..2.200854 s. Markers therefore identify source scheduling, not measured speech onset/offset. The author's minimum correlation, peak-ratio and separation tolerances are heuristic search rules, explicitly not target-presence thresholds or calibrated uncertainty.

Cross-channel start/end peak spreads reach 98/99 samples (about 2.06 ms). Apparent affine scale is -416.7..-53.9 ppm for 0-degree first take, +1509.8..+1764.7 ppm for second take, and approximately +515..+578 ppm elsewhere. With common acquisition channels, differing peak lags/scales can involve acoustic transfer, competing peaks, phone playback/DSP and unknown clocks; these figures must not be interpreted as independently measured sample-rate drift or channel synchronization errors. The available evidence cannot disambiguate the cause. Two-point fitting necessarily fits both anchors and is not an independent validation of intermediate timing.

For developer-only exploratory statistics, results.json provides the intersection of the four source-mapped speech intervals and an optional inner 200 ms guard on each side:

| Take | Inner candidate core, seconds from capture start |
|---|---|
| 0 first | 2.352646..3.152146 |
| 0 second | 2.069521..2.871604 |
| -45 first | 2.099688..2.899104 |
| -45 second | 1.928646..2.729708 |
| +45 first | 2.186125..2.987417 |
| +45 second | 1.994479..2.795771 |

The guard is analyst-selected, arbitrary and uncalibrated. These ranges exclude scheduled chirps with substantial separation but do not establish that all reverberation is absent or that speech is continuously active. They are not scoring labels. Frames used for exploratory comparisons must lie wholly inside the chosen interval; do not include chirp frames or extrapolate target-presence accuracy over entire captures. Keep original PCM and shared channel timing; do not align channels independently for direction evaluation.

Limited PASS for marker reproducibility and candidate source-time mapping as development aids. Precise acoustic boundaries, boundary uncertainty, room decay, phone timing, channel mapping/synchronization and direction accuracy remain unverified. No listening, new acquisition, build, hardware run, SNR gain or M1/H3 claim is made. Main review owns overall signal and target-presence diagnostics.
