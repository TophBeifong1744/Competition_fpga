# B review evidence, 2026-09-14

Decision: both candidates **NEEDS_FIX**, no implementation approved or merged.
Read the [independent review and A repair handoff](../../../docs/maintenance/skills-review-b-2026-09-14.md).

Reviewed commits:

- SKL-001: `c562466805aff08201cd457cc2e6ee7464a3566f`.
- SKL-002: `55039cf8bfab2bd6112192c8bd646d427a52a642`.

Raw bytes are preserved. `manifest.json` binds every retained evidence file except itself. `verify_archive.py` checks it. Original command records retain historical absolute paths; they are provenance, not paths that a new machine must have. `reproduce.py` supplies portable replay for the reported faults, using separately checked-out exact candidates and a new output directory. This evidence is not a second active Skill or production RTL source. Synthetic `.bit` / `.hwh` fixtures are non-deployable test inputs.

| Directory / file | Purpose |
| --- | --- |
| `skl001-unit`, `skl001-examples`, `xsim-examples` | B-run unit tests, actual XSim normal/fault/restored demonstrations |
| `forward` | Blind task requirements, authored TB, original/fixed/X/Z run snapshots, visible correction report |
| `b-golden`, `xsim-b-golden` | B-only mathematical golden and actual exhaustive RTL output trace, 65,536 comparisons |
| `latency-mutant`, `xsim-latency-mutant` | Candidate TB falsely passes a two-stage implementation under the one-stage contract |
| `b-latency-*`, `xsim-b-latency-*` | Independent contract witness: correct one-stage RTL passes, two-stage mutant fails |
| `skl002-required`, `skl002-unit`, `skl002-receive`, `skl002-timeout` | Required commands and raw 50-test / receive / retained-timeout results |
| `skl002-independent`, `skl002-cli-*` | Two synthetic profiles, external golden, lifecycle faults, IP mismatch / duplicate-evidence false PASS |
| `evidence-audit.json`, `skl*-structure` | Source/log/manifest binding and actual system quick_validate outcomes |
| `closeout.json` | Local/remote identities and materials disposition |

Runtime of portable replay: Python standard library; XSim replay requires actual Vivado 2025.2. No board access, PYNQ import, network, installation or production build is needed. Board guard remains intact. Mock clock values are not measured hardware speed. Timing, CDC, implementation, board and system acceptance remain NOT_RUN.

Owned B scripts, test RTL/TB and generated synthetic inputs follow the repository [MIT license](../../../LICENSE). Snapshotted candidate files retain their exact original bytes and attribution; their provenance is the reviewed commit and source hashes. Author historical logs are referenced in the candidate, not rewritten here. The copied blind Skill itself and reproducible simulator `work/` caches are omitted; use the exact candidate and recorded commands to restore them. The original B acquisition/checkpoint files remain local and do not contain another implementation.
