# 板级候选独立复核回执

2026-10-10，由协调者归档各只读复核者的实际返回结论。原始测试文件、失败及修复记录保留，不把修复前候选改写成通过。

## 控制、结果存储和 PWM 门控

非作者复核：`/root/pwm_evidence_review`，最终 **PASS**，仅限新增模块 FUNCTIONAL_SIM 和已审静态集成范围。

当前板级快照 aggregate：`94ec3200c0a2e9c0ba3c4e701804a9e8decdd8ef9136edcedfa2d594cc55cefc`。早先 `41f3696c…` 与此快照的全部 36 项 RTL 散列一致，变化仅为接口说明补充，允许复用相应功能证据。

- 控制：76 项独立检查完成。
- 完整证据保存、逐字读取和握手：2529 项检查完成。
- PWM 门控和真实角度映射模块：2918 项检查完成。
- CONTROL_CHECK、DATA_CHECK、GATE_MAP_CHECK 均有实际触发的隔离负例，不依赖仿真进程 exit 0。
- C-VIO-STATIC-001（前端先结束导致提前撤许可）、C-VIO-STATIC-002（恢复使用旧 IDLE 提前完成）、C-VIO-EVID-003（门控检查器负例缺失）均由非作者判定 VERIFIED_CLOSED。

原件：`../board-prep/board-verification/`。修复1索引 `TEST-SNAPSHOT-repair1.json` SHA256 为 `b02d27a37b7616cc65b701d05f6b824d408514adce294edd71c2496f9209a38f`；门控补测索引 `GATE-CANARY-INDEX.json` SHA256 为 `77bb31a0cf8ae2238cea96735dc0e27f9f1642eb51c3f126df37b2759d2c11d4`。

边界模型检查控制及保存行为，没有假造 FFT/IP 模型来签算法或整机通过。完整核心与官方 IP 联合展开/仿真、综合实现、bit/LTX 和实物行为不在本 PASS 范围。

## 时钟、复位和约束

只读专项：`/root/c_board_cdc_constraints`。实际 wrapper、PWM gate、引脚和窄 CDC 例外检查 **无阻断数字综合/实现的静态问题**；STA_COVERAGE 仍 UNVERIFIED。

全部新逻辑、VIO/ILA、算法和双轴 PWM 使用同一 61.44 MHz。保留三级同步释放复位；只切断四个麦克风输入到各自首级同步寄存器 D，不切下游或相关时钟关系。ASYNC_REG 布尔检查接受 1/true。

综合网表真实对象、相关 MMCM 自动派生时钟、实际约束覆盖和 PDM 外部有效窗仍须原生报告或现场证据，未在此编造通过。现用 C 转接板图纸 L/R=GND 与采样相位一致，实装与剩余约30.208ns预算未实测。

## 用户接入入口

专项复核 `/root/vio_ip_contract_review` 已完成，结论 **PREFLIGHT_READY_FOR_USER_EXECUTION**。C-IP-VIO-001（独立 Tcl elseif 命令）已由定向旧版复现和新版三分支检查关闭。新状态显示及 banks 读取与 RTL 位图一致。

IP 快照 aggregate：`1e2864805a47aaca78621bb67926e097ac32191621ec431b97b26d7db24713e4`。

- `prepare_i17_vio_gui.tcl` SHA256：`6f335b5661e9a9b927e6a169abd6ce74b0976fc02ec7b69b16a6228e622a4df2`。
- `hardware_i17_vio.tcl` SHA256：`1810f52cef425178c708dc78d7d6bb984e588fcc7920e21f269698a703c85a15`。

可以交由用户 source 导入，出现 `C_I17_VIO_READY` 后展开，无阻断错误再综合、实现。Tcl mock 不是 Vivado/IP 实跑；实际硬件探针属性、跨 JTAG 采样新鲜度、完整官方 IP 生成和工程结果尚未验证。本结论不签执行器动作或整机通过。用户的准确入口和保存点见《[新操作单-VIO板级工程](新操作单-VIO板级工程.md)》。

## 2026-10-11：C-IP-VIO-002 增量复核

用户原生运行在创建 VIO 后因 `IP_PART_UNPROVEN i17_board_vio` 停止。真实 VIO XCI 不含 FFT 的 `model_parameters.C_PART`，但正式 `project_parameters` 中 DEVICE=xc7z020、PACKAGE=clg400、SPEEDGRADE=-1 完整一致；原正则校验误拒绝。以上旧候选及其复核记录保留，以下为此次修复的新候选。

非作者 `/root/vio_ip_contract_review` 返回 **PREFLIGHT_READY_FOR_USER_RETRY**，C-IP-VIO-002 在脚本校验修复范围关闭。脚本 SHA256：`b5538fdd559429adde9bd5dbfbacdb8bb3bd9a9bbaa7e989eb6dc0765f8f3d46`；IP 快照 aggregate：`d131e384ba1ac24bb808632eed84eddf140e3c98d404e382fa8d45be7223a0ba`。

- 复核者核对快照文件哈希和真实 D 盘 VIO/FFT XCI 副本一致，并独立执行既有 `check-target.tcl`。
- 真实 VIO、FFT 和 C_PART-only 证明通过；错速度级、冲突、缺失、重复、多值、错误层级、截断及尾随数据被拒绝。
- 器件字段按 JSON 类型及准确层级读取；C_PART 与项目器件三元组同时存在时均须匹配。原源文件和生成目录归属检查保留。
- 当前工程是合法部分创建状态：正确 VIO 已登记，ILA 尚未创建，板级源/约束尚未替换。可验证并复用 VIO，沿原入口继续，不删除、不 force、不重建。

证据与原失败副本：`../board-prep/ip-repair2-check/`；修复说明：`../board-prep/IP-REPAIR-2.md`。未修改产品 RTL 或 D 盘用户工程，不重复未变化的 RTL 回归。真实 Vivado 重跑、新 ILA 及产品生成、OOC、完整展开、综合实现和硬件动作仍待原生证据；合成的 ILA 结构测试不代表真实 ILA 已生成。
