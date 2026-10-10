# Installation

[README](../../README.md) · [Simplified Chinese](../zh-CN/installation.md) · [Architecture](architecture.md) · [Roles](roles.md) · [Usage](usage.md) · [Safety and evidence](safety-and-evidence.md)

## Prerequisites

- Windows with [PowerShell 7](https://learn.microsoft.com/powershell/) available as `pwsh`.
- A local clone or downloaded copy of this repository.
- A Codex environment that supports custom agents under `.codex/agents/` and skills under `.agents/skills/`.
- Write permission for the selected user or project target.

The package does not install an FPGA vendor toolchain, Python modules, Node packages, drivers, board files, or vendor IP. No new dependency is downloaded by the scripts.

## 1. Validate the package

From the repository root:

```powershell
pwsh -NoProfile -File .\scripts\validate-package.ps1
```

This performs package-level structural and public-content checks. It does not run an FPGA compiler, simulation, implementation, STA, CDC/RDC analysis, or board test.

## 2. Preview before writing

Both user and project installation support PowerShell's `-WhatIf` preview.

```powershell
# User scope preview
pwsh -NoProfile -File .\scripts\install.ps1 -Scope User -WhatIf

# Project scope preview
pwsh -NoProfile -File .\scripts\install.ps1 -Scope Project `
  -ProjectPath C:\path\to\repo -WhatIf
```

Review the exact target paths before running without `-WhatIf`, especially if the target already contains custom agents or a workflow skill with the same names.

## 3. Choose an installation scope

### User scope

Use user scope when you want the roles available across FPGA repositories:

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 -Scope User
pwsh -NoProfile -File .\scripts\verify-install.ps1 -Scope User
```

The default targets are:

```text
<UserProfile>/.codex/agents/*.toml
<UserProfile>/.agents/skills/run-fpga-workflow/**
<UserProfile>/.codex/codex-fpga-engineering-workflow.install.json
```

### Project scope

Use project scope for repository-local behavior or evaluation without changing user-level role files:

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 `
  -Scope Project `
  -ProjectPath C:\path\to\repo

pwsh -NoProfile -File .\scripts\verify-install.ps1 `
  -Scope Project `
  -ProjectPath C:\path\to\repo
```

The targets are the same relative locations under the selected project root.

## Optional AGENTS.md template

By default, installation deploys only the 13 agent definitions and the workflow skill. It does **not** install or overwrite an `AGENTS.md` file.

To opt in at project scope:

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 `
  -Scope Project `
  -ProjectPath C:\path\to\repo `
  -InstallAgentsTemplate
```

This maps `templates/AGENTS.fpga.md` to the project's `AGENTS.md`. At user scope, the template target is `<UserProfile>/.codex/AGENTS.md`. Read the template before installing it: repository-specific rules and project facts should normally remain in the project, and an existing `AGENTS.md` may contain instructions that must be preserved.

## Existing files, refusal, and backup

The installer computes SHA-256 for every source and destination:

- identical existing content is left in place;
- different existing content causes a refusal by default;
- `-Force` permits replacement only after creating a timestamped backup next to the destination;
- the install manifest records each path, installed hash, and backup path.

Use `-Force` only after reviewing the target and backup plan:

```powershell
pwsh -NoProfile -File .\scripts\install.ps1 `
  -Scope Project `
  -ProjectPath C:\path\to\repo `
  -Force
```

`-Force` is not a merge operation. If you have local role customizations, preserve them in version control or a separate copy and re-apply them deliberately after the upgrade.

## Verify the installed files

The verification script checks the install manifest, the recorded SHA-256 values, all 13 workflow agent files, and the installed skill entrypoint:

```powershell
pwsh -NoProfile -File .\scripts\verify-install.ps1 -Scope User
```

or:

```powershell
pwsh -NoProfile -File .\scripts\verify-install.ps1 `
  -Scope Project `
  -ProjectPath C:\path\to\repo
```

Start a new Codex session after installation so discovery occurs from a clean session. Then use a harmless read-only prompt such as:

```text
Use $run-fpga-workflow in ANALYZE mode. List the applicable workflow roles and
explain which project evidence you would read before reviewing an RTL change.
Do not modify files.
```

File verification is not the same as fresh-session behavior. Version 0.4.0 statically validates role/schema/template routing, while identity-card and live-task behavior in each real target remains evidence to exercise in that project.

## Create a standard FPGA project

The package can create a clean local project scaffold without installing an EDA tool:

```powershell
pwsh -NoProfile -File .\scripts\new-fpga-project.ps1 `
  -Destination C:\work\my-fpga `
  -ProjectName my-fpga `
  -TopModule top `
  -Vendor XILINX
```

Use `PANGO` or `ANLOGIC` for those targets. The scaffold records stable project identity, emits a fail-closed `project/script/run.bat`, and keeps `simulation/script` at exactly `run.bat`, `setting.txt`, `src_list.txt`, and `vsim.do`. Add one confirmed vendor Tcl/CLI flow beside the build BAT; generated export scripts, libraries, logs, and waves remain under `simulation/work`. The real launcher must be a depth-0 `project/par/<project-name>.xpr|.pds|.al`, never a nested `par/vivado_project` or `par/build` project. Configure a tool root/vendor environment, use only a process-local PATH, and invoke canonical commands by name rather than embedding absolute executable files.

## Upgrade

1. Fetch or download the desired tagged package version.
2. Read [CHANGELOG.md](../../CHANGELOG.md) and [COMPATIBILITY.md](../../COMPATIBILITY.md).
3. Run package validation in the new package.
4. Preview installation with the same scope and project path used originally.
5. If files differ, inspect them and run with `-Force` only when replacement is intended; timestamped backups are created.
6. Run `verify-install.ps1`.
7. Start a new Codex session and perform a read-only discovery check.

Pinning a release is recommended because Codex custom-agent, skill, and plugin schemas may evolve.

## Uninstall

Preview first:

```powershell
pwsh -NoProfile -File .\scripts\uninstall.ps1 -Scope User -WhatIf
```

Then uninstall:

```powershell
pwsh -NoProfile -File .\scripts\uninstall.ps1 -Scope User
```

For project scope:

```powershell
pwsh -NoProfile -File .\scripts\uninstall.ps1 `
  -Scope Project `
  -ProjectPath C:\path\to\repo
```

The uninstaller:

- accepts only paths recorded by this package's install manifest;
- resolves every candidate beneath the exact selected root;
- removes only files whose current SHA-256 still matches the installed hash;
- preserves modified files and retains the manifest for audit when any are kept;
- does not remove backup files automatically; and
- never recursively deletes a directory tree.

## Safe boundaries and troubleshooting

- The installer cannot merge custom role prompts. A content mismatch requires review.
- The optional template can affect every task in its scope; install it only where that behavior is wanted.
- A project-level `AGENTS.md` may supplement or tighten user-level rules. Resolve any conflict before relying on the workflow.
- Installation verification proves file presence and integrity, not role behavior or FPGA correctness.
- If a verification error reports `Modified`, compare that file with the package before deciding whether to keep, merge, or force-replace it.
- If a role is not discovered, confirm the selected scope, restart Codex, verify the target paths, and check current Codex documentation for schema changes.

After installation, continue with the [mode and prompt guide](usage.md).
