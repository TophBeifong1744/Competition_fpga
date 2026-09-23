# Vivado 工程

成员间保留 [H1 最小接口 → H2 首批诊断数据 → H3 算法包集成评审](../document/three-handoff-workflow.md)。A/B/C 按 Issue 承担工程开发和合格非作者复核；具体职责见[现行分工](../document/team-tasks.md)。以下冻结/阶段门用于对应接板、正式集成或验收声明，不禁止独立离线工作。

本目录当前只有活动 RTL、README 和 add_sources.tcl。正式工程仍为仓库外的 one/one.xpr，target/source view 按[工程身份](../document/project-identity.md)核对；project_entry=null、adapter_status=UNVERIFIED。本次不创建工程、不导入或连线、不综合实现。native_project 的必要 .xpr/.srcs/IP 不能通配当缓存，生成物按[文件保留规则](../document/generated-artifacts.md)分类。

团队已固定使用 Vivado `2025.2`。当前只表示工具版本决策完成，不表示 SoundSight 已在该版本完成脚本重建、仿真、综合、实现、时序收敛或板上运行。

RTL 接入统一遵守 [语言与 BD 接入约定](../task-packages/PKG-A-H3-INTEGRATION/references/policy/rtl-language-and-bd-integration.md)：简单模块用 `.v`；复杂 `.sv` 核心通过 `.v` 实例化包装后作为 Module Reference 添加到 BD。不得仅修改文件扩展名，也不得将该模块设为整个 BD 工程顶层；仿真和综合通过不替代实际 BD 验证。

当前入口：

```text
project/
  rtl/                 # 活动模块库
  add_sources.tcl      # 仅由用户按授权向已打开工程添加三件基础 RTL
```

日后获准规范化正式工程时，launcher 必须直接位于 project/par/<name>.xpr，同名数据库为其直接同级；正式 build/runtime 规则按锁定工程 Skill 执行。本次没有这些受控输入或真实 launcher，故不创建空目录、空 BAT 或占位工程。

构建流程必须为 `.bit`、`.hwh` 和 XSA 记录同一 Git 提交、目标 part/board、Vivado 版本、接口版本和文件哈希；禁止混用不同构建的 `.bit` 与 `.hwh`。PL 只暴露后端无关的 AXI4-Lite、AXI DMA 和中断合同，不得因 PYNQ 的 Python 类名或 Notebook 流程改变核心 RTL。具体交付要求见 [PYNQ 集成与控制面指南](../document/pynq-integration-guide.md)。

每次候选构建至少保存：

- Vivado `2025.2` 的实际版本输出、构建主机/环境标识、Git 提交和完整 part；
- 从空构建目录执行的入口命令、日志、退出码和产物哈希；
- 自检仿真的输入、golden、实际输出和 PASS/FAIL；
- 综合与实现的 utilization、timing summary、clock、CDC/DRC 和关键警告结论；
- 与该构建匹配的板级工程、部署/运行脚本、原始实测输出及 golden 对比。

最终发布包把受控源码与脚本映射到 `src/`、`sim/`、`build/` 和 `board/`；生成目录、官方 PDF、内部会议材料和许可不明文件不直接复制。发布包必须在纯英文路径中完成从零重建，并通过匿名/隐私、绝对路径和许可证检查。
