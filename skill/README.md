# Competition Skills Index

This directory contains reusable Skills prepared from the competition project's actual engineering workflow. Skill documentation and static validation are not evidence that the FPGA system, timing, or hardware has passed.

## Skills

| Skill | Purpose | Availability | Validation status |
|---|---|---|---|
| [soundsight-engineering-workflow](soundsight-engineering-workflow/README.md) ([entrypoint](soundsight-engineering-workflow/SKILL.md)) | Evidence-gated FPGA/embedded workflow from requirements and hardware freeze through reproducible delivery and failure review | Available | System validation and current-M0 forward scenario passed; hardware outcomes remain unverified |
| [pynq-overlay-dma-validation](pynq-overlay-dma-validation/README.md) ([entrypoint](pynq-overlay-dma-validation/SKILL.md)) | Profile-driven Overlay, AXI4-Lite, DMA/cache, golden-reference, performance, and resource validation | Available | System validation and 5/5 offline/mock cases passed; real-board validation remains pending |

## Competition-requirement mapping

| Requirement | Location or evidence | Status |
|---|---|---|
| Reusable Skill with accurate discovery metadata and bounded instructions | `soundsight-engineering-workflow/SKILL.md` | Implemented |
| Submission README covering use, failure conditions, verified effect, and limits | `soundsight-engineering-workflow/README.md` | Implemented |
| Each Skill item identifies the failures or observations it came from | `soundsight-engineering-workflow/README.md`, section “Failures and observations behind the Skill” | Implemented with concrete project and validation observations |
| Evidence, gate, four-class verification, reproducible-run, AI-visible interaction, and failure templates | `soundsight-engineering-workflow/references/record-templates.md` | Implemented |
| Large-model collaboration record with prompts, answers, and visible self-correction | Skill entrypoint and AI interaction template | Implemented; hidden chain-of-thought is neither available nor submitted |
| Real or isolated forward test | Current SoundSight M0/G1 scenario in the Skill README | Passed as a workflow test; not a hardware test |
| System Skill validation | `quick_validate.py` against the Skill directory | Passed |
| Vivado/Vitis version | AMD guide permits `2026.1` (recommended) or `2025.2`; SoundSight is fixed at `2025.2` | Compliant |
| Complete engineering package: source, verification, implementation reports, board output/reference comparison, and reproducible build | Covered by G3-G6 and the record templates | Workflow coverage implemented; project artifacts remain unverified |
| Board and exact-device declaration | G1 and G5 require exact identity plus real-board output | Not passed for SoundSight; full part/speed grade and board evidence remain incomplete |
| Open-source and redistributable license | Repository `LICENSE` is MIT; G0 records licensing constraints | Present; final submitted contents still need a license and third-party-material audit |
| Skill location, README, use, failure conditions, verified effect, and boundaries | `skill/` index and linked Skill documentation | Implemented |
| Reproducibility-safe path names | Owned Skill paths use ASCII names; required `README.md` and `SKILL.md` filenames are retained | Owned files passed; the repository as a whole has existing non-English/special-character paths and has not passed final submission-path audit |
| Recommended repository layout or README directory mapping | Project root README documents the current directory roles | Present; final submission package must be rechecked against the AMD guide |
| Submission anonymity from the separate competition FAQ | Final team name, report, video, and demonstration must exclude school information, logos, and map location | Separate FAQ requirement; not attributed to the AMD selection guide |
| Junior-division eligibility | AMD guide: first- through third-year undergraduates; mixed teams follow the highest member | Current three-member input is consistent; official student-status review remains authoritative |
| Second Skill integration | [pynq-overlay-dma-validation](pynq-overlay-dma-validation/README.md) | Implemented as an offline/mock-validated v0; board evidence remains pending |

## Current project boundary

For SoundSight, the board is currently identifiable as the `ATK-DF7010P_7020P` series with baseboard `V3.9` and Zynq `XC7Z020` device family, and Vivado is fixed at `2025.2`. Full speed grade, PYNQ image/support, DDR, final pins/clocks, and the four-channel acquisition path still require M0 evidence. These items are not passed by creating this Skill.
