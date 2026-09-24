# FPGA module development and verification Skill

2026-09-23 contest-export candidate. Its implementation baseline is the exact
B-approved `a7e1ea976da91ba735af5c0a79fffdc7d10c121f`; the approved scope is module
development and actual XSim simulation. This export adds portable naming,
bundles the attributed PCM source, and records fresh candidate execution. It
does not change the approved runner, elastic RTL or testbench behavior.

The submitted entry is lowercase `skill.md`. To install it in a tool that
requires the canonical filename, copy or rename it to `SKILL.md` without
changing its bytes. `license.txt` contains the MIT license for this package.

The 2026-09-14 S1 repair found that ordered transaction comparisons did not
enforce the one-edge/one-slot contract.
The TB now checks occupancy, valid, ready and valid payload before/after each
edge, plus reset-discard accounting. The original two-stage mutant still
reproduces the old false PASS (1149 checks); the repaired TB rejects it at
cycle 2 after the first accepted edge. Correct/restored elastic runs pass
13800 actual checks, not the historical 1125 below. The runner retains data
and ready faults and adds a two-stage fault. See the package-local
[correction index](references/correction-index.md) for the exact historical
commits, results and reuse boundary. The current approval and this candidate's
new execution are summarized by the parent delivery README; historical source
manifests and logs retain their original identity.

SKL-001 supersedes the retired workflow-only Skill. This package remains a
module-level tool and example set; it is not production RTL or hardware proof.

## Purpose and use

Use [skill.md](skill.md) to develop/debug a bounded module: interface and numeric contract → RTL → independently justified self-checking TB → actual XSim execution → first-failure analysis → scoped correction and retest. Team review rules support this technical loop; they are no longer the main product.

Give the agent the module request, allowed edit paths, existing sources/contract and simulator version. It should read the Skill and relevant reference, implement only the requested scope, then return code, actual commands/results and limitations. For an unfamiliar team, use the standalone non-acoustic elastic example. The PCM example includes one attributed, version-bound copy of the C-authored module so this export runs without the parent repository.

From this exported Skill directory with Python 3.10+ and Vivado 2025.2:

```text
python -B -m unittest discover -s tests -v
python -B scripts/run_examples.py --vivado-bin F:/AMD/2025.2/Vivado/bin --output ../new-evidence/xsim
```

Use a new output directory. Replace the explicit tool path for another installation; do not accidentally use an older PATH version. The runner supports standalone `.v`/`.sv`, not VHDL, IP simulation libraries or arbitrary Tcl projects. It opens no existing Vivado project and does not synthesize, constrain or program hardware. No external subSkill is required; all Python runtime helpers use the standard library.

## Verified effect and failures

On Windows/Python 3.12.14 and actual Vivado XSim 2025.2, author tests produced (the system Skill validator separately used Python 3.14.6):

| Run | Actual result | What this supports |
| --- | --- | --- |
| Bundled pcm4_signext_pack, widths2/24/32 | PASS, 792 word comparisons | Interface/sign-extension test on the attributed project module; not room acoustics |
| Non-acoustic elastic stage, widths1/8/16 | PASS, 13800 checks | Contract/TB/runner reuse across a different module; stall/reset/full-rate behavior |
| Deliberately flip one output bit in a disposable DUT | FAIL at first compared transaction | TB detects this data fault; failure is expected test evidence |
| Deliberately prevent empty-stage acceptance | FAIL at empty acceptance | Directed contract check detects a throughput/handshake defect |
| Restore the correct DUT, unchanged test inputs | PASS, 13800 checks | Fault evidence preserved and same-case retest executes |

Raw commands, source snapshots, first failures and result hashes are indexed by
the parent candidate delivery. Runner unit tests also check absent/duplicate PASS,
late fatal, zero checks, wrong version, failed tools, missing input, timeout
classification and refusing old output directories. See
[the correction index](references/correction-index.md) for the approved historical
failures and held-out signed8 case. Windows was executed; other OS/Python versions
are not certified.

## Derivation and own contribution

- The user identified that the old Skill mostly said what evidence should exist without teaching/executing the RTL/TB work. The correction is a narrow technical workflow, actual runner and two reproducible module examples; old evidence was archived unchanged rather than relabeled as new technical validation.
- Existing project work established separate compile/elaborate/run records and source manifests. This candidate generalizes the case configuration, requires positive assertions, keeps the first failure and refuses stale output directories. It does not infer hardware success from a log or a push.
- The two deliberate faults demonstrate why data comparison alone is insufficient: the second needs an explicit acceptance/throughput assertion. The failures were intentionally injected, not falsely described as historical field defects.
- Structural/static validation is not behavioral quality. B still needs an unfamiliar module/request, a held-out fault and actual use without this chat. No percentage improvement in AI productivity or token use is claimed.

## Limits, ownership and license

Single-clock/combination module workflow only. CDC, full AXI protocol, vendor-IP libraries, fixed-point algorithm derivation, synthesis/timing/board acceptance and full-system integration need additional task-specific work. The elastic example is a reference module, not a production replacement. It has combinational ready, not a registered-ready timing guarantee.

Owned new files follow the repository MIT license. The bundled PCM module is
the unmodified C-authored C-RTL-003 source identified in
[its local contract](examples/pcm4/contract.md); it is included so this export
is runnable without the parent repository. The system skill-creator and
xilinx-suite were authoring aids, not copied dependencies or the team's
original contribution. No third-party Skill scripts were installed or
incorporated.

For contest submission, preserve visible user/AI corrections in the task report;
do not submit hidden reasoning. The parent delivery binds this export to a file
manifest and fresh run. Static structure, author execution, independent approval
and hardware validation remain separate results.
