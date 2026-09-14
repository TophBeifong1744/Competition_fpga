# PKG-A-SKILLS：工程协作 Skill 0.2.0 候选

作者：A 拓芙 / 本工程协作任务。技术复核与批准后合入：B BryanZheng802，或获本次明确授权的主流程。C无新增任务。

本包本轮仅交SKL-001和根索引的配套候选，不包含SKL-002源码，不代表两个Skill整体完成。状态在 [REVIEW.md](REVIEW.md) 登记；作者自检不能变为B批准。

## 版本和范围

- 版本：0.2.0；起始本地HEAD：`80bd2c723eac803eb8bbbddd96369d8e9d2a543c`。本任务不查询远端、不创建分支、不提交/推送/合并。
- 只写本包；`payload/`按将来总工程目标相对路径放置。活动区`skill/`保持原样，PYNQ起始未审改动保留。没有核心RTL/Vivado/PS/硬件/归档证据修改。
- 第一项仍名为soundsight-engineering-workflow，通用规则不固化项目人数、麦数、日期、文档名、器件或后端。
- 完整批准身份由最终 [MANIFEST.json](MANIFEST.json) 的外部SHA-256绑定；清单不包含自身。工作执行推送后补真实远端SHA，再交B复核，不填虚构提交号。

## 目录和入口

| 路径 | 内容/用途 |
|---|---|
| [payload/skill/soundsight-engineering-workflow](payload/skill/soundsight-engineering-workflow/README.md) | 可交给其他团队使用的Skill、竞赛README及可选模板 |
| [payload/skill/README.md](payload/skill/README.md) | 根索引候选；PYNQ和项目文档链接按最终安装目标解析，不复制依赖 |
| [evidence/acceptance-plan.md](evidence/acceptance-plan.md) | 执行前冻结的行为判据 |
| [evidence/migration-input.md](evidence/migration-input.md) | 非声学项目的隔离输入；不是真实硬件数据 |
| [evidence/verify_package.py](evidence/verify_package.py) | 本交付只读完整性验证器，不是Skill必需运行时或批准工具 |
| [evidence/test_verify_package.py](evidence/test_verify_package.py) | 临时字节夹具的破坏/恢复测试，不接触现有项目原件 |
| [manifest.md](manifest.md) | 目标路径、依赖、版本保护及清单范围 |
| [report-material.md](report-material.md) | 可见人机纠正、失败与报告写法 |
| [HANDOFF.md](HANDOFF.md) | 给工作执行任务的发布/请B复核说明 |

## 自检/复核命令

以下在仓库根运行，Python 3.10+、标准库；实际本机采用Python3.14。所有命令加`-B`避免产生pycache。

```text
python -B -m unittest discover -s task-packages/PKG-A-SKILLS/evidence -p test_verify_package.py -v
python -B task-packages/PKG-A-SKILLS/evidence/verify_package.py task-packages/PKG-A-SKILLS
python -B <skill-creator>/scripts/quick_validate.py task-packages/PKG-A-SKILLS/payload/skill/soundsight-engineering-workflow
```

最后一项需要system skill-creator及PyYAML；本机使用`C:/Python314/python.exe`。缺工具时报告环境问题，不修改Skill或降级判据来刷PASS。清单用于检测缺件/多件/原字节变化，不能认证人工批准或物理来源。

行为测试不能由上述命令替代：请新评估任务仅读取指定Skill及migration-input.md并实际回答A～D，不提供acceptance-plan或旧答案；与本包完整可见输出对照判据。真实案例读取本包source-snapshot中的指定现行材料，按固定版本复跑；若主线变更，须先区分历史复现与最新状态评估。

## 发布与未覆盖项

正常下一步是工作执行检查本包、推送完整待审任务分支、提供准确远端SHA和本清单哈希给B。B批准准确范围后由指定合入者处理4个目标文件，在新位置做链接/结构/适用检查，并立即按team-workflow做实际共享main、跟踪main、直接远端main和本批有用材料核对。未审PYNQ不得夹带，不重跑历史FFT/录音或阶段验收。

本包无硬件运行、无PYNQ探针解除保护、无模型/RTL/时序/声学新结果，无B人工批准或实际发布。9/25完整Skill目标是项目计划，不是本包已实现的整项验收。
