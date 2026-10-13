---
name: run-fpga-workflow
description: Design, implement and integrate FPGA and firmware from system budgets and independent expectations to same-candidate physical reports, early bounded board validation and reproducible delivery.
---

# System-driven FPGA implementation

Work inside the current system goal and S1 requirements / S2 joint design / S3 development / S4 integration / S5 system validation / S6 delivery. Team size changes allocation, never technical completion criteria. Reuse applicable results and runnable integration entries; do not restart successful stages or impose six approval gates.

## Design before expansion

For new or materially expanded modules, establish applicable input and measurement rules, interface/ownership, numeric formats, clocks/reset/CDC, memory/port/bandwidth, resource and throughput/deadline budgets. Derive them from the end-to-end configuration including public IP, interconnect and debug. Numerical chains use MATLAB or existing equivalent floating/fixed models; control paths use state/protocol/recovery analysis. Compare only needed alternatives, then implement the selected feasible design. Critical design changes use project decision authority; unchanged choices and equivalent repairs do not ask again.

Whole-design resources include all real linked instances; never sum parent and child twice, substitute black boxes for capacity, equate operation counts with instantiated hardware, or label estimates as measured. Feedback from synthesis/implementation corrects budgets. Known capacity/deadline infeasibility returns to the affected architecture before adding functionality. Do not invent universal reserve percentages, coverage targets or endurance hours.

## Implement and prove the affected behavior

ANALYZE is read-only, QUICK bounded maintenance, FULL substantial new behavior. These choose depth, not mandatory roles/chats. When using supplied role agents, only `fpga_engineer` writes product RTL/build/constraints; `embedded_engineer` writes assigned firmware. One writer per writable checkout/EDA output; product/test mutations in separate assigned phases. Authors cannot independently approve their own implementation or material test contribution. A qualified non-author context starts from requirements and raw evidence, not a full inherited author conversation; it may continue incremental repairs.

Authorized project-owned RTL/BD recipes/XDC/IP configurations/firmware can be edited; vendor products are formally generated. Verify primitive/IP semantics against actual target/tool and official material when needed. Distinguish stable single-bit levels, pulses, related multibit data and reset release; Gray is not a generic bus fix. Initialization and arithmetic support depend on target/tool and required runtime behavior, not blanket bans.

Independent expected values must not merely duplicate DUT assumptions. Target key numerical, protocol, stop/restart, ownership and boundary behavior; canary changed critical checkers when needed and reuse valid coverage. Exit zero/PASS does not override Fatal, missing stimulus or ineffective comparison. Separate product, test, helper and environment failures. Do not run unrelated long simulation matrices.

## Integrate and test the actual configuration

Join runnable endpoints as soon as the interface is clear; the authoritative project is a candidate and entry, not a permanent monopoly by one person. Purposeful isolated builds/OOC/incremental reuse are allowed; do not rebuild the full project for every handoff. Major integration checks actual hierarchy/whole-board resources, budget deviation, constraints/CDC/RDC/DRC, and applicable routed setup/hold. Synthesis WNS is not physical closure; missing/stale/mismatched reports and parser errors are not zero violations.

Plan board observation at dispatch: relevant real signals, sampling clock, trigger/window, known input and correct/error criteria, debug cost and matching bit/LTX. First bounded board validation follows the first testable chain with required implementation/timing/safety; subsequent significant joins are batched. Human build/programming/wiring/reset/motion obey project authorization. Field data goes directly to analysis and identified faults to the responsible implementation, without coordinator approval detours.

Board-discovered fault repair skips this simulation and prioritizes the same board reproducer after required new build, affected timing/CDC and electrical/motion checks. Record skipped, not PASS. This does not exempt new functionality or known major risks. Future regression follows repeatability/impact, not a compulsory debt gate for every skipped simulation.

## Identity, delivery and termination

Preserve dirty/untracked/ignored useful work; no reset/clean/stash/force-push. Bind actual sources/dirty inputs/config/IP/XDC/macros/tool to build ID, then generated artifact hashes and applicable board identity readback; never embed a final artifact hash into itself. Short SHA/date/readback alone does not prove full logic or functionality.

Retain concise failure summaries and only raw evidence needed for unresolved diagnosis, difficult reacquisition or quantitative acceptance. Do not preserve every failed run forever or delete by suffix/age. Major node delivery is a complete relocatable Vivado/Vitis ZIP; small repairs use exact increments to the existing project. Actual opening is required to claim it opened. Ordinary version differences are recorded, actual incompatibility is handled when observed.

Merge after necessary checks and qualified non-author judgment within existing authority; scoped merge does not close untested system goals. Stop at most three automatic repair/re-review rounds or two consecutive no-progress rounds; retain problem identity/counts and report next responsible entry/recovery conditions. New effective input or changed cause/plan and authority are needed to resume, not a new name/model.

Use the existing project paths; for new normalized layouts, project/par and simulation/work are formal outputs, codex_out diagnostic. A depth-0 launcher and process PATH are options after verifying entry, never grounds to migrate an existing project. Share actual tool/CPU/memory capacity: target at least half logical CPUs and near-full useful parallel work where supported, record real tool caps/serial limits; do not create dummy work, interrupt runs or change global settings.

## Read only applicable references

[System design](references/system-development.md) · [Module method](references/module-development.md) · [Human/ILA](references/human-checkpoints-and-ila.md).
Technical schemas and lookup resources below are optional tools, not another mandatory packet or review chain:
[profiles](references/task-profiles.md), [artifacts](references/workflow-artifacts.md), [temporal](references/temporal-evidence.md), [model](references/model-card.md), [vendor](references/vendor-adapters.md), [layout](references/project-layout.md), [identity](references/project-identity-and-task-delta.md), [IP](references/ip-integration.md), [physical](references/physical-implementation.md), [faults](references/private-fault-library.md), [shadow](references/shadow-rollout.md), [improvement](references/improvement-policy.md), [evidence](references/improvement-evidence.md).
