# Contributing

Contributions are welcome.

1. Open an issue describing the workflow gap and evidence.
2. Keep roles narrowly scoped and preserve single-writer ownership.
3. Add or update tests in `scripts/validate-package.ps1` for structural changes.
4. Avoid private paths, customer facts, device-specific assumptions, and claims not backed by reports.
5. Run package validation and include the command, environment, result, and remaining `UNVERIFIED` items in the pull request.
6. Keep runtime roles, Skill instructions, schemas, and scripts in English. Maintain Simplified Chinese documentation only under `README.zh-CN.md` and `docs/zh-CN/`, and keep language-switch links working.

Changes that relax electrical safety, CDC/RDC, STA, licensing, single-writer, or reviewer-independence controls require explicit maintainer approval.
