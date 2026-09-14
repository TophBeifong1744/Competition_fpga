# Isolated forward module execution report

Actual result: corrected sat_add passes XSim 2025.2 behavioral simulation. Original fails; disposable X and Z output mutants fail as expected. No Skill approval or comparative quality score is issued.

## Scope and visible operations

Read only supplied forward/sat_add.sv and forward/skill/SKILL.md plus its references/rtl-and-tb.md, references/xsim-and-debug.md, scripts/run_xsim.py. No parent-directory material, author answer, production project, Git, network, board, software install or privilege escalation was used. Python and Vivado executable paths were supplied by the task. All authored evidence stays in forward/.

1. Read supplied RTL and Skill before implementation. Noticed suspicious lower saturation constant but did not edit original RTL.
2. Authored contract.md, tb_sat_add.sv and case.json from task requirements. Golden interprets signed 8-bit operands as integers, adds in integer domain and clips to decimal limits. Scoreboard models a one-entry transaction queue, compares old output before accepting its replacement and checks post-NBA state. Stimulus is generated deterministically within the snapshotted TB; no external vector files.
3. Ran unmodified supplied RTL first into runs/01_original. Compile and elaboration succeeded; actual simulation failed at cycle 3, transaction 1, 36 ns: a=-128 b=-1 expected=-128 actual=-127 (10000001).
4. Located negative overflow branch: 9-bit sum -129 is correctly below -128, but assigned -127. Changed only RTL constant `y<=-8'sd127;` to `y<=8'sh80;` (signed 8-bit -128), see rtl-fix.diff. No TB, manifest, contract or input/seed change.
5. Reran same case into new runs/02_fixed; PASS_SIMULATION. Read actual compile, elaboration and runtime logs. TB/manifest/contract hashes identical to first run.
6. Created disposable copies under mutants/x and mutants/z that replace lower saturation output with eight X or Z bits. Same TB, contract and case content. Both real simulations compiled/elaborated and failed at cycle 3, reporting the unknown payload without numeric coercion. Corrected main RTL remains untouched.
7. Preserved all run directories, source/contract/manifest snapshots, logs, simulator work and result.json. Verified recorded hash identities and result states; no evidence directory overwritten.

## Executed coverage

`SKILL_PASS cases=66343 checks=337372`

`COVER accepted=66343 consumed=66341 discarded=2 stalls=890 replaces=66084 fullrate=65536 seed=57124abc`

- Exhaustive 256 x 256 signed operand pairs at one acceptance per cycle: all sign combinations, -256/+254 exact sums, both clipping boundaries and neighboring values.
- Cycle-level registered validity/payload and combinational-ready checks; no artificial extra pipeline allowance. 65,536 continuous full-rate inputs, simultaneous consume/replace, empty acceptance while downstream stalled, directed 32-cycle stall and fixed LCG traffic (2,048 cycles).
- Active-high synchronous reset clears valid/y, repeated reset, in-flight reset both with stalled output and with ready high. Exactly two pending transactions discarded. Producer keeps offers stable until acceptance or reset.
- Invalid and reset-discarded operands exercise both X and Z; accepted unknown operands are explicitly unsupported and rejected by checker. Known valid output data and controls use case inequality. Separate X/Z output mutants verify detector sensitivity.
- Pipeline drains; accepted = consumed + reset-discarded; minimum checks/cases and coverage guards; 1 ms watchdog, normal finish at 676336 ns.

## Run outcomes

| Run | Actual status | First observation |
|---|---|---|
| 01_original | FAIL_SIMULATION | SKILL_FAIL cycle=3 id=1 expected=-128 actual=-127 bits=10000001 pending=1 a=-128 b=-1: post-edge numeric/hold |
| 02_fixed | PASS_SIMULATION | 66343 cases / 337372 checks |
| 03_mutant_x | FAIL_SIMULATION | SKILL_FAIL cycle=3 id=1 expected=-128 actual=x bits=xxxxxxxx pending=1 a=-128 b=-1: post-edge numeric/hold |
| 03_mutant_z | FAIL_SIMULATION | SKILL_FAIL cycle=3 id=1 expected=-128 actual=z bits=zzzzzzzz pending=1 a=-128 b=-1: post-edge numeric/hold |

## Commands and tool identity

Python 3.13.0, Windows; Vivado Simulator v2025.2, XSim SW Build 6299465. Supplied Skill runner used unchanged, default per-stage timeout 90 seconds. Exact top-level commands are also in commands.txt. Each run/result.json records each actual xvlog/xelab/xsim argv, cwd, return code, timing, source hash and log hash.

```text
D:/Python/python.exe -B F:/NUEC/review-evidence/skills-b-20260914/forward/skill/scripts/run_xsim.py --case F:/NUEC/review-evidence/skills-b-20260914/forward/case.json --vivado-bin D:/AMD/2025.2/Vivado/bin --output F:/NUEC/review-evidence/skills-b-20260914/forward/runs/01_original
D:/Python/python.exe -B F:/NUEC/review-evidence/skills-b-20260914/forward/skill/scripts/run_xsim.py --case F:/NUEC/review-evidence/skills-b-20260914/forward/case.json --vivado-bin D:/AMD/2025.2/Vivado/bin --output F:/NUEC/review-evidence/skills-b-20260914/forward/runs/02_fixed
D:/Python/python.exe -B F:/NUEC/review-evidence/skills-b-20260914/forward/skill/scripts/run_xsim.py --case F:/NUEC/review-evidence/skills-b-20260914/forward/mutants/x/case.json --vivado-bin D:/AMD/2025.2/Vivado/bin --output F:/NUEC/review-evidence/skills-b-20260914/forward/runs/03_mutant_x
D:/Python/python.exe -B F:/NUEC/review-evidence/skills-b-20260914/forward/skill/scripts/run_xsim.py --case F:/NUEC/review-evidence/skills-b-20260914/forward/mutants/z/case.json --vivado-bin D:/AMD/2025.2/Vivado/bin --output F:/NUEC/review-evidence/skills-b-20260914/forward/runs/03_mutant_z
```

## Source identity (SHA-256)

- original RTL: `5bcf79c303c2ddfdfcf5cfcf7762fc9acae9f42bef6b3086756da316b7ef7400`
- fixed RTL: `3f43ff7f4c0a8ccee06ca7a1803c9c811d7dc12bdccf1fb788d3e839d4307029`
- unchanged TB: `93de8a5ef812f215888519ffef0ae7dca301a286e2c691ae5a538a5ed8fc21ac`
- unchanged manifest: `fca79d59b8fc5030259e0cdd63df6947c0e87d4168eef225dfa625f169227a5f`
- unchanged contract: `20ca308455886e3a725368a7a9f17a03485c6bed7f1c693f035efbbc42e80e67`
- unchanged runner: `80eabf73d614898636fcc599844c714480987cea66ee9e0bdbbc710f36a144e6`

## Remaining boundaries

Behavioral simulation only. Synthesis, implementation, constraints, STA/timing, CDC, board and system tests: NOT_RUN. Exhaustive arithmetic is not exhaustive temporal-state formal proof; random traffic uses one fixed seed. Accepted X/Z operands and unknown handshake/reset controls have no functional arithmetic contract; not claimed supported. Mutants establish detection of injected X/Z payload defects only, not exhaustive checker mutation coverage. Invalid output y is unspecified except reset. This is an 8-bit one-clock module; other widths, clocks and vendor IP are not tested.
