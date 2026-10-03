# #19 双轴定角新候选交审入口（2026-10-03）

按 [I19-CURRENT-STOP-01](https://github.com/TophBeifong1744/Competition_fpga/issues/19#issuecomment-5967609218) 复用本次已有工作，交付新增顶层/XDC、参数限幅和 FUNCTIONAL_SIM 证据。原始验证快照为 `sha256:2fea207c93d1358ca7908d350a9190488acc9fdc058307a272100eb97ac51c48`。准确发布 Git 候选 SHA 由 PR 提供；本包不是历史实载证明，不扩张旧 #19 批准范围。

产品入口见 [使用说明](../../servo-dual-test-20261003.md)：仓库既有 v2 `motor_drive.v` + 新 `servo_dual_test_top.v` + 新 `servo_dual_test.xdc`。两轴信号 T15/W16，时钟 U18/50 MHz；水平目标限于 0–360°、垂直 40–220°。完整电气量程分别 360°、220°；启动位置分别 180°、130°。

| 场景 | 本候选代码支持的行为 | 证据/限制 |
|---|---|---|
| 配置启动 | 16 拍内部复位释放；第 17 沿开始首个 PWM 周期并接受一次静态目标 | 首周期 180°/130°；目标在第二周期生效，组合仿真覆盖 |
| 无新有效命令 | 保持已经锁存的目标，持续输出 PWM | 本顶层只有启动一次命令，无运行时输入；不能推断机械停止 |
| 合法静态参数 | 映射到各轴完整电气量程的 500–2500 us，20 ms 周期 | 6 场景覆盖默认、端点和中间值 |
| 参数越界 | 有符号整数先限幅，再转 9 位：水平 0–360、垂直 40–220 | 负值/1024 超量程场景覆盖 |
| 时钟停止 | 时序逻辑无法继续更新，PWM 电平可能停在最后状态 | 无时钟丢失检测/自动安全关断；实际停钟与机械响应 NOT RUN |
| 禁用/停止/制动 | 无相应端口或协议 | 没有运行时 reset、TTL、紧急停止或机械制动，不能宣称已验证 |

本候选不含声源方向转换或动态角度总线、寄存器/IRQ/DMA及到位反馈。LCD 对 T15/W16 的既有占用必须在独立工程中排除。仓库与旧 D 盘 XPR 的器件速度等级 `-2`/`-1` 差异仍未解决；没有创建 XPR 或修改实际 D 盘工程。

## 已有验证与真实接收边界

XSim 2025.2 原生 compile/elaborate/run：50 MHz、6 场景、各 3 个 PWM 周期、54,000,306 次信号比较，正常 `TEST_PASS`。脉宽/周期/启动沿/有效沿四个 canary 均预期断言失败。负向 XSim 进程状态可能仍为 0，语义失败见原生日志及 [结果索引](verification-results.json)。

[独立 AI 最终复核](FINAL-REVIEW.md) 已完成，限 FUNCTIONAL_SIM，不能代替 A 的非作者成员接收。[源码复核](source-review.md)、[问题台账](findings-ledger.json)、[仿真证据](simulation-evidence.json)、[模式检查](artifact-schema-check.json) 为同一验证材料。本候选综合、实现、STA、新下载与实板运动均 **NOT RUN**，当前未作新 BOARD 或阶段总通过结论。

## 原始资料与可访问记录

本包 `logs/` 保存最终正常运行及四个 `_wavefixed` 负向运行的原生 compile/elaborate/run 日志，字节不变，仅把 `.log` 文件名改为 `.txt` 便于 Git 保存。[copy-provenance.json](copy-provenance.json) 给出原名、发布路径、字节数和原文件 SHA256；[package-manifest.json](package-manifest.json) 列出本包文件原始字节哈希。

`codex_out/issue19-dual-top-20261003` 路径只是 C 机原始来源，审查可直接使用本包已发布的小型日志。WDB/缓存/可执行文件未上传，波形仍留在 C 机，其身份见仿真证据。原始 snapshot 哈希对应实际编译文件；Windows CRLF 与发布 Git blob LF 可能造成字节哈希不同，准确 Git blob 映射由发布清单另列，不把差异写成源码变化或重新运行。
