# Evidence-triggered physical implementation

Read this reference only for `IMPLEMENTATION_QOR` or `TIMING_CLOSURE`, or when
actual post-place/post-route reports show a physical problem. Do not apply it
to ordinary source review, compile, simulation smoke, or unrelated RTL changes.

## Closed loop

1. Freeze tool/version, part, source/constraint snapshot, seed, and strategy.
2. Establish synth/place/route baseline reports.
3. Classify the highest-impact failing paths or implementation bottleneck.
4. Change one primary variable.
5. Rerun the required implementation stage.
6. Compare WNS/TNS, hold, route status, congestion, resources, and runtime.
7. Keep evidence-backed improvements; otherwise revert.
8. Repeat only within the bounded repair budget.

## Classification

```text
logic depth
route delay / placement distance
high fanout
congestion
clocking
RAM/DSP/GT/IO placement
CDC-adjacent physical path
constraint coverage or precedence
```

Choose the owner from evidence. Do not default to changing seed/strategy,
adding Pblocks, floorplanning the whole design, repeated phys-opt, register
replication, or pipeline insertion. There is no cross-device global logic-level
or slack threshold.

## Power boundary

Power is NOT APPLICABLE by default. Run formal power analysis only when the
user requests it or a real power/thermal/safety/release budget requires it.
When used, state activity provenance; do not turn power into a routine gate.
