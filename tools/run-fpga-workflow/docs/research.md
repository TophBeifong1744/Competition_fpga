# Open-source research record

Research date: **2026-08-24**. Dynamic metrics below are a point-in-time snapshot and may be stale. Commit IDs are intentionally recorded as supplied research baselines; verify the full SHA before vendoring or compliance work. No candidate code was copied into this repository.

## Method

Candidates were compared on Codex/plugin format fit, multi-agent structure, test/CI evidence, documentation and reproducibility, maintenance, licensing clarity, and adaptation cost. Stars/forks are auxiliary popularity signals, not quality proof. FPGA safety, CDC/RDC, STA, single-writer ownership, and independent sign-off were designed for this repository rather than inferred from popularity.

| Candidate | Snapshot | License | Decision and reason |
|---|---:|---|---|
| [openai/plugins](https://github.com/openai/plugins) | commit `11c74d6...`; 5,192 stars; 728 forks | No license asserted in this snapshot | **Architecture reference only** for current plugin/skill packaging; licensing uncertainty prevents code reuse. |
| [openai/codex](https://github.com/openai/codex) | commit `2df670...`; 116,096 stars; 17,703 forks; release `rust-v0.149.1` | Apache-2.0 | **Primary ecosystem reference** for Codex concepts and maintenance signals; not an FPGA workflow. |
| [NVIDIA/skills](https://github.com/NVIDIA/skills) | commit `7149a8...`; 3,079 stars; 358 forks | Apache-2.0 | **Skill-structure comparison**; useful packaging ideas, but no FPGA engineering gate model. |
| [wshobson/agents](https://github.com/wshobson/agents) | commit `d82998...`; 39,064 stars; 4,164 forks | MIT | **Role-catalog comparison**; broad agent coverage, but this repository needs stricter single-writer/evidence separation. |
| [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | commit `ebe9c9...`; 147,680 stars; 23,842 forks | MIT | **Persona/documentation comparison**; not adopted because detailed FPGA lifecycle and EDA evidence gates are absent. |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | commit `d8409a...`; 242,673 stars; 36,728 forks; release `v2.1.0` | MIT | **Workflow/prompt comparison**; not reused because its focus and evidence model differ from FPGA sign-off. |
| [github/spec-kit](https://github.com/github/spec-kit) | commit `27f50f...`; 131,001 stars; 11,766 forks; release `v1.0.1` | MIT | **Requirements/specification inspiration**; adapted conceptually as Requirement -> Design -> Test traceability, with no copied code. |
| [Thinklab-SJTU/Awesome-LLM4EDA](https://github.com/Thinklab-SJTU/Awesome-LLM4EDA) | commit `5be3a4...`; 295 stars; 32 forks | NOASSERTION | **Domain landscape only**; curated research links are not an installable, licensed workflow implementation. |

The earlier `openai/skills` repository is deprecated; current ecosystem comparison uses [openai/plugins](https://github.com/openai/plugins). Official product behavior should be checked against current [OpenAI Codex documentation](https://developers.openai.com/codex/).

## Source-level conclusions

The strongest references cover different layers rather than one complete solution: OpenAI repositories best match the host packaging ecosystem; spec-kit demonstrates structured specification; general agent catalogs demonstrate role decomposition; LLM4EDA maps the research landscape. None provides the required combination of FPGA project SSOT, one product writer, stable-diff supervision, isolated EDA databases, CDC/RDC and STA evidence, register/IRQ/DMA contracts, safe board actions, and independent sign-off. Therefore this repository implements those rules from first principles and only borrows high-level organization ideas.

## Why search stopped

Eight candidates covered the current Codex/plugin format, skill packaging, general multi-agent role libraries, specification-driven development, and LLM-for-EDA research. Additional broad agent collections were no longer changing the selected architecture or the main risk register. The remaining uncertainty is product-schema evolution and fresh-session discovery, handled through compatibility notes and static validation rather than more unrelated candidates.

## Known limits

- Metrics, releases, and repository state are dynamic; query date is 2026-08-24.
- `openai/plugins` licensing was not asserted in the supplied snapshot, so no code is reused.
- End-to-end Codex discovery, FPGA EDA execution, timing closure, and board safety are UNVERIFIED by this research record.
