# Independent contract baseline
Read contract.md before author-result.json.
Confirmed requirement: signed 8-bit saturating addition, output range [-128,127].
Independent rule: clamp(integer(a) + integer(b), -128, 127), for signed 8-bit operands.
Examples: 100+40 -> 127; -100 + -40 -> -128; 50 + -20 -> 30; 127+0 ->127; -128+0 -> -128.
Unknown: cycle timing, reset, hardware target, RTL, exact source commit, EDA entry and evidence; not required to establish this numerical counterexample.
Mode ANALYZE; no FPGA execution, code change, hardware, global installation/configuration or remote write authorized.
