# C 当前 VIO 工程：交 A/B 优化的源快照（2026-10-11）

本包对应 C 本机 `i17_vio_board_top` 实际进行综合的工程。36 个 RTL、2 个 XDC、Hann 初始化文件和 4 个官方 XCI 原件均保持字节不变；重新组织路径并补齐配置、责任边界和原始日志，便于 A/B 定位并优化。

**交付状态：源码与证据交接，综合未完成，未生成 bit，不是上板放行。** 本批没有改算法、缓存、STOP、时钟或协议，也没有启动/取消原工程。原 XPR 仅作证据，不能当另一台机器的可直接打开工程。

- 主目标：Vivado 2025.2 / `xc7z020clg400-1` / `i17_vio_board_top`。
- 实际路线：50→96→61.44 MHz；四麦→前端 FFT→B 后端/IFFT→角度映射→舵机；VIO/ILA 操作和观察；每次显式 START 只授权一个真实窗口。
- 本快照没有 PS/BD/Vitis，也没有自动连续重启。后来远端 PS/连续控制规划及新 A STOP 候选未混入这次实际运行快照。
- 入口：先读 [优化交接与已知问题](document/optimization-handoff.md)，重新建工程按 [手动导入操作单](document/manual-vivado.md)。完整配置在 [project-settings.json](project/project-settings.json)。

| 目录/文件 | 用途 |
|---|---|
| `project/rtl/` | 实际 36 个产品源文件；每个文件只有一份活动副本 |
| `project/script/src_list.txt` | 原生综合读入顺序映射到本包；只是文件列表，不是导入脚本 |
| `project/sdc/` | 2 个真实约束；CDC 文件仅 implementation 使用 |
| `project/data/hann-u18f17.mem` | Hann 原字节；HANN_FILE 必须改为新机器绝对路径 |
| `project/ip/reference-only/` | 4 个真实官方 XCI 原件，带旧输出路径，禁止就地生成 |
| `project/ip/config/` | 原 XCI 提取的全部 component/model/project/runtime 参数 |
| `simulation/tb/`、`simulation/reference/` | 有界 C 控制/存储/PWM 测试与旧 PWM 对照模型，不加入 Design Sources |
| `evidence/synthesis/` | 11:33 固定的历史诊断，含两次旧会话；保留原始 native log/Tcl/XPR |
| `evidence/synthesis/latest-observed/` | 另存 13:03 新启动会话的日志和原生入口；不覆盖旧证据 |
| `evidence/tests/`、`evidence/provenance/` | 已有有限测试、复核、父候选与 B 身份记录；不是本次新 PASS |
| `source-map.json` | 原始绝对路径→包内相对路径、逐文件 SHA256/大小/归属 |
| `manifest.json`、`verify_package.py` | 静态内容清单和只读完整性检查，由交付方负责核验 |

当前观察及全部限定见 [handoff-status.json](document/handoff-status.json)。截至本包捕获，13:03 新会话日志最后处于 Timing Optimization，没有完成结果；无法推算剩余时间。此前 13:01 的 132 分钟仅属于 10:49 旧会话，不能当新会话时长。

本包没有 `.bit/.ltx/.dcp`、工具缓存或可直接运行的 `.xpr`。接收者可立即审代码和日志；同版 Vivado 重建、完整综合、资源/STA/板测仍需后续执行并保存原件。
