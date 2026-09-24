# Scripts

本目录保存跨模块、可重复执行的检查与构建入口，例如测试向量生成、仿真回归、Vivado 批处理、报告摘要和结果归档。

脚本要求：

- 从仓库根目录调用，不依赖个人绝对路径。
- 失败返回非零状态并指出失败阶段。
- 记录工具版本、输入参数和随机种子。
- 不自动覆盖已确认的 `results/` 记录；生成物写入被忽略的临时目录，经复核后再归档。

## 复核自动检查的复用入口（2026-09-17）

执行[六项增量复核](../document/team-workflow.md#review-efficiency)。先由复核人依据合同和差异选检查，再使用**准确候选内**的已有入口；下表是现有实现的定位示例，不是每批必跑清单，也不替代包内版本/环境要求。

| 范围 | 已有入口 |
| --- | --- |
| FPGA Skill 示例仿真 | [run_module_skill_examples.py](run_module_skill_examples.py) 为当前布局适配入口，仅派生 case 并调用原 run_xsim.py；旧 run_examples.py 全演示按准确旧 SHA 复现 |
| PYNQ Skill 离线用例 | [run_offline_tests.py](../skill/pynq-overlay-dma-validation/scripts/run_offline_tests.py)、[simulate_dma.py](../skill/pynq-overlay-dma-validation/scripts/simulate_dma.py)；仅 mock，不做真实 DMA |
| B 三路离线音频 | [reproduce.py](../task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/reproduce.py)、[verify_package.py](../task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/verify_package.py) |
| E1 固定归档 | [reproduce.py](../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/publication/reproduce.py)、[package_manifest.py](../task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/endurance-test-01/publication/package_manifest.py)；仅按批准范围和记录环境运行 |

每轮一次汇总命令、环境、用例/检查数量、结果、预期负例阶段、失败首错及原日志路径；模型按需打开异常日志，不重复输出整份成功日志。可直接在既有 REVIEW 中填写[一页入口](../docs/templates/review-brief.md)，不要求改写旧 JSON 格式或另建通用运行器。

迁移后的调用：`python -B scripts/run_module_skill_examples.py --case all --vivado-bin <Vivado-bin> --output codex_out/skill-examples-new`。--prepare-only 仅生成派生 case；--case 可选 pcm4、elastic、all。合同/TB/原 runner 不改，输出只接受 codex_out 下全新目录；该入口只作路径诊断，不重签 Skill 或模块批准。H1 fixture 检查仍用 `python -B scripts/check_h1_fixtures.py`。

Git 差异、准确版本、清单/哈希和本批本地材料核对使用既有脚本或固定命令；技术批准另行签署。没有复核过的脚本及超出解析器能力的输入不能仅凭退出码当通过。命令涉及构建、下载或硬件时，继续遵守 AGENTS.md 的用户操作与授权边界。
