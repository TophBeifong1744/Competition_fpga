# Vivado 工程

执行规则更新（2026-09-08）：成员间仅 [H1 最小接口 → H2 首批诊断数据 → H3 算法包集成评审](../docs/three-handoff-workflow.md)。暂定接口可版本化用于工程框架、读取器、逻辑/TB和离线算法开发；短实录不等一小时长稳，但只作诊断。A/B 负责技术开发和判断，C 只[按操作单](../docs/member-c-operation-sheet.md)执行。以下冻结/阶段门用于对应接板、正式集成或验收声明，不禁止独立离线工作；完整包交付而非逐小动作审批。

本目录保存可复现工程所需的 Tcl、XDC、Block Design Tcl 和必要 IP 配置；本机生成的 `.xpr`、runs、cache、bitstream 和硬件导出文件不进入 Git。PYNQ 采用同一次构建生成的 `.bit` 与 `.hwh` 作为 Overlay，XSA 继续用于 Vitis/PetaLinux 后端和硬件平台复现。

团队已固定使用 Vivado `2025.2`。当前只表示工具版本决策完成，不表示 SoundSight 已在该版本完成脚本重建、仿真、综合、实现、时序收敛或板上运行。

预期入口：

```text
vivado/
  create_project.tcl   # 后续生成：从受控源码重建工程
  constraints/         # 板级与时序约束
  bd/                  # Block Design Tcl
  ip/                  # 必要且可审计的 IP 配置
  reports/             # 小型构建摘要模板
```

创建首个工程时，应把目标器件/板卡、Vivado 版本、顶层模块、源文件和约束全部写入脚本，并在干净目录验证可重建性。

构建流程必须为 `.bit`、`.hwh` 和 XSA 记录同一 Git 提交、目标 part/board、Vivado 版本、接口版本和文件哈希；禁止混用不同构建的 `.bit` 与 `.hwh`。PL 只暴露后端无关的 AXI4-Lite、AXI DMA 和中断合同，不得因 PYNQ 的 Python 类名或 Notebook 流程改变核心 RTL。具体交付要求见 [PYNQ 集成与控制面指南](../docs/pynq-integration-guide.md)。

每次候选构建至少保存：

- Vivado `2025.2` 的实际版本输出、构建主机/环境标识、Git 提交和完整 part；
- 从空构建目录执行的入口命令、日志、退出码和产物哈希；
- 自检仿真的输入、golden、实际输出和 PASS/FAIL；
- 综合与实现的 utilization、timing summary、clock、CDC/DRC 和关键警告结论；
- 与该构建匹配的板级工程、部署/运行脚本、原始实测输出及 golden 对比。

最终发布包把受控源码与脚本映射到 `src/`、`sim/`、`build/` 和 `board/`；生成目录、官方 PDF、内部会议材料和许可不明文件不直接复制。发布包必须在纯英文路径中完成从零重建，并通过匿名/隐私、绝对路径和许可证检查。
