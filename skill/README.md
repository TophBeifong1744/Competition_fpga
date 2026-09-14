# Competition Skills Index

SKL-002 has independent B approval for its offline implementation; SKL-001 repair review is in progress. Skill execution, author tests, B approval and main publication are separate; neither Skill proves full FPGA-system or board acceptance.

| ID / Skill | Actual purpose | Current status |
| --- | --- | --- |
| SKL-001 [fpga-module-verification candidate](../docs/maintenance/skills-publication-2026-09-14.md#skl-001) | Module contract, RTL/self-checking TB development, real XSim execution, first failure and repair/retest | 0.3.0 author candidate: 792/1125 normal checks, two rejected DUT faults and restored PASS; B held-out use/review pending |
| SKL-002 [pynq-overlay-dma-validation](pynq-overlay-dma-validation/README.md) | Profile-driven Overlay checks and mock DMA lifecycle validation | B PASS (offline only), exact 3ac597d; 55 tests / 57 subtests and 14 independent sessions; real PYNQ NOT_RUN |

Approval and evidence: [B repair review](../docs/maintenance/skills-rereview-b-2026-09-14.md). SKL-002 is active at its approved offline scope. SKL-001 remains on its exact repaired candidate until its separate decision. Historical candidate publication records remain unchanged below their current-status notice.

Use the [delivery/acceptance plan](../docs/skills-delivery-plan.md) for requirements, dates, ownership, limitations, licensing and submission export. A develops, B independently reviews; C has no additional Skill task. Full source/test/effect/provenance and visible AI correction records are needed, not just README files. Generic PYNQ bonus is explicitly in the guide; no fixed score is guaranteed.

The old workflow-only Skill and its 0.2.0 unreviewed package are [archived byte-for-byte](../archive/2026-09-13-before-skl001-technical-upgrade/README.md). They are not active alternatives. Keep one maintained source per Skill; retained run inputs are evidence snapshots, not another development tree.

Current hardware/algorithm status belongs in [current-status](../docs/current-status.md), not a historical Skill example. Vivado is fixed at 2025.2, actual part is xc7z020clg400-2; diagnostic captures exist, but formal M1/full H3/real-time/accuracy/audio and PYNQ qualification are separate unfinished gates.
