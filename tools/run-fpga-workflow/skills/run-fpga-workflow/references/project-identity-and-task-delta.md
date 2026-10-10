# Project identity baseline and live task delta

Use this reference when a user supplies an FPGA project identity card, when a
new project or target is opened, or when a later request changes the active
task. The identity card reduces discovery cost; it is not a frozen all-purpose
specification and does not grant broad write or external-operation authority.

## Stable project identity

Normalize only relatively stable facts:

```text
project_root
canonical_project_entry
vendor
tool / tool_version
part
product_top / simulation_top
build / simulation / lint entrypoints
long-term protected boundaries
board boundary
```

Treat user-provided values as declared intent until confirmed from the project
or tool. Keep project-specific facts in project AGENTS/SSOT, not user-level
roles, Skill text, Memory, or cross-project defaults.

## Live task state

For every substantive follow-up, derive:

```text
current_task
task_delta.relation = INITIAL | SUPPLEMENTS | SUPERSEDES | EXPANDS | NARROWS
authorization
protected_work
requested_claim
claim_stage
impact cone
role routing with mode and reason
```

The latest explicit request updates the current task. It does not silently
remove sticky protected boundaries or authorize clean/overwrite, IP
regeneration, implementation, release, external publishing, or physical board
actions.

## Incremental refresh

Do not rescan the machine or regenerate a full opening report for an ordinary
follow-up in the same project. Refresh only changed files, the affected cone,
coupled verification assets, constraints, IP, scripts, and evidence.

Refresh project identity when evidence shows a material change to the project
root, canonical launcher, vendor, part, top, board revision, tool/IP version,
source/constraint target view, or requested claim stage. An ordinary code
commit or clarification within the same target updates the snapshot, not the
whole identity card.

## Precedence

```text
safety and cross-project hard gates
project SSOT and current observed evidence
latest explicit user request
stable identity-card defaults
history and inference
```

Report conflicts rather than silently selecting one source. If an identity
card says one tool version and the actual command reports another, stop
version-sensitive IP or implementation acceptance until resolved.

Power is NOT APPLICABLE by default unless an explicit request or real
power/thermal/safety/release budget activates it.
