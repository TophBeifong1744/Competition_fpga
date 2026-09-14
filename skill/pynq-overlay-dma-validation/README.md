# PYNQ Overlay 与 DMA 通用验收 Skill

本轮交付是**可执行、可测试的离线 v0 收口**：新增 DMA 生命周期核心与 CPU/设备分离内存模型，修复异常、缓存所有权及释放时机；不具备真实 PYNQ 板测能力。

## 适用场景与赛题定位

对应仓库 AMD 选题指南的通用 PYNQ Skill 方向：Overlay/寄存器/DMA 验收、典型故障定位、golden 对比和性能/资源证据整理。具体映射见 [验证状态](references/validation-status.md)。不承诺固定加分，不替代 RTL、时序和真实上板结果。

PYNQ 是首选但可替换的控制、调试、展示与验收层，不是实时声学算法的执行基础。本项目现有 Vitis standalone 路径继续有效；PYNQ 准入不满足时不阻塞 PL 核心，用同一 AXI 合同接入 Vitis/PetaLinux。

## 当前输入与缺项

只读核对发现：当前 XSA 配置为 **simple S2MM-only，无 MM2S、无 DRE**，不能直接套双向 loopback。已有 compiled PS 合同、HWH 参数和 DDR 范围可提取；但它们不是 PYNQ 分配器或驱动的上板证明。

[输入审计](references/input-audit.md)列出了来源、哈希、可复用项与缺项。实际工程常量只出现在这份案例审计，不进入通用逻辑。完整部署 profile 尚不能从这些材料自动生成。

## 用法

在本 Skill 目录运行；所有输出使用新的文件名：

```sh
python -B scripts/simulate_dma.py --contract references/example-session.json --output results/receive.json
python -B scripts/simulate_dma.py --contract references/example-session.json --fault timeout --fault abort-timeout --output results/timeout.json
python -B scripts/run_offline_tests.py --output results/tests.json
```

第一条执行纯内存单向接收并对比合成参考；第二条应退出 1，报告 FAIL/retained，证明超时不误释放；第三条运行全部回归并记录源码哈希。要测试双向回环，把你自己的合同中 `transfer.mode` 改为 `loopback`，无需改脚本。

现有工具继续用于项目提供的材料：

```sh
python -B scripts/validate_profile.py --profile <profile.json> --mode offline --output <new-static-report.json>
python -B scripts/compare_golden.py --expected <golden.bin> --actual <capture.bin> --format bytes --output <new-golden-report.json>
```

完整 profile 与离线生命周期合同不是同一种输入：
[profile 合同](references/profile-contract.md)针对构建身份与 loopback 证据结构；
[生命周期合同](references/lifecycle-contract.md)针对独立的单向/双向 DMA 软件行为。
示例 profile 的 bit/HWH 只是待填写路径；示例 session 可直接离线运行。

## 实际实现与验证

- `scripts/dma_session.py`：分配即持有；部分启动即按 DMA 可能持有处理；异常先留状态；有授权才请求 abort；确认静止后释放，否则保留。
- `scripts/simulate_dma.py`：CPU/设备独立字节数组、可注入故障、单向接收/回环；可复现漏 flush/invalidate 导致的真实字节差异。
- `scripts/run_offline_tests.py`：逐测试结果、源码哈希、环境和证据等级。
- 测试覆盖分配/提交/缓存/状态/超时/取消/实际包长/重试阻断/重复传输/释放异常；另保留原有 profile 与 golden 回归。
- 地址对齐与传输长度粒度已分离，允许如 64 字节地址对齐、96 字节传输、8 字节长度粒度的合法组合。
- golden 数值对比保留 JSON 整数精度，避免大整数转浮点及容差溢出造成误判；JSON 小数仍按 Python 的 binary64 浮点解析，不是任意精度十进制模型。
- `pynq_probe.py` 保留拒绝上板入口，已移除保护后面的不安全旧原型；真正的离线修复位于上述可运行核心，不以“禁用”代替测试。

最新实际结果见 [验证状态](references/validation-status.md)和随附的离线测试报告。报告只证明 static/mock，不是任何板卡通过、B 复核或整机验收。

## 失败条件与当前边界

合同错误、状态不可读/过期、部分启动异常、DMA 错误、超时、缓存操作失败、实际长度错误、golden 不符或释放不确定均为 FAIL；失败会阻断同一 session 的下一次执行。无法确认静止时不读、不释放，保留对象也不代表真实硬件进程退出安全。

还没有：真实 PYNQ 驱动适配器、Overlay 下载/寄存器实读写、真实 TLAST/中断、SG/cyclic、长稳、实测吞吐延迟或新 Vivado 资源/时序证明。静态 full profile 目前仍要求 loopback 与 RO 身份合同；不能伪造 MM2S/身份寄存器让实际采集工程通过。

上板准入、故障定位与待测矩阵见 [板测清单](references/hardware-runbook.md)。本轮未改 RTL、Vivado、XDC、现有 Vitis 程序，未连接板卡、未提交 Git。

## 可复用性与比赛报告

脱离 SoundSight 的复用证据是：两套不同器件/IP/寄存器/流宽的合成 profile，以及两种传输方向、多种长度和缓存策略，均由输入驱动同一代码。它证明参数化软件复用，**不证明第二块实板已通过**。任意算法的 golden 模型和 payload schema 由项目另行提供。

报告可写：“完成 profile 驱动的 Overlay 静态验收与 DMA 生命周期故障注入工具；通过所附离线回归，明确分离 static/mock/hardware 证据。真实 PYNQ 驱动、回环和性能验证待板测。”附实际测试报告、故障案例、第二套合成输入及上板缺项。不要写成“已完成 PYNQ 移植”或“已测得硬件吞吐”。

交给 B 的范围、复跑命令和判定口径见 [复核说明](references/review-handoff.md)。
