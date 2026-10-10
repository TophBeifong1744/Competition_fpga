# Private fault-library hook

This package reserves an optional local diagnostic index for private after-sales incident documents. It does not contain or upload those documents.

The local configuration points to a user-controlled source outside the public repository. Imported cases use `references/schemas/fault-case.schema.json` and one of these states:

`IMPORTED`, `ROOT_CAUSE_CONFIRMED`, `FIX_VERIFIED`, `BOARD_CONFIRMED`, `REUSABLE`, or `REJECTED`.

A case becomes `REUSABLE` only after the source document, root cause, repair, verification evidence hashes, applicability, counterexamples, independent review, and board disposition are non-empty. Board disposition contains actual confirmation evidence or `NOT_APPLICABLE:<reason>`. A match is a lead, never proof for the current project; re-check vendor/tool/version, subsystem, clock/reset, interface, IP mode, trigger, applicability, and counterexamples.

Use `scripts/fault-library.ps1` to create an empty local configuration, validate sanitized case JSON, or query indexed cases. Query output goes to `codex_out/<run-id>/knowledge/`. Never store customer identity, proprietary RTL, private paths, secrets, board-specific values, or historical pass claims in this public package, generated Memory, or global prompts.
