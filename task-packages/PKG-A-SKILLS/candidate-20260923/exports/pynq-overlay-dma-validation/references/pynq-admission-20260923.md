# 2026-09-23 PYNQ admission report

结论：**BLOCKED**。当前只有可运行的 static/mock 候选，没有足够证据进入真实
PYNQ Overlay/DMA 操作；Vitis standalone 四路采集主线不受此结论影响。

## 逐项结论

| 准入项 | 当前事实 | 结论 |
| --- | --- | --- |
| 板卡及器件 | 已有资料指向 ATK-DF7010P/7020P 系列、V3.9 底板；当前构建声明为 `xc7z020clg400-2`。尚无本轮从实物丝印/芯片ID独立读取的证据 | BLOCKED：精确物理板卡/核心板修订与器件身份未独立绑定 |
| PYNQ 镜像/板级支持 | 没有已启动且证明兼容该底板 DDR、MIO、启动介质及网络的版本化 PYNQ 镜像，也没有板级支持包的批准记录 | BLOCKED |
| 同构建 bit/HWH/manifest | Vitis 路线已有 Vivado 2025.2 XSA，历史审计 SHA-256 为 `71e7bf6d4fcb769582e5485660515b8f615b2027aa2ff18c1f8d3f67f9457baa`；XSA/HWH声明 simple S2MM-only、无 MM2S/SG/DRE、32-bit AXIS、64-bit memory、14-bit length。但没有为 PYNQ 准备并验证一套相邻、同构建、带manifest的可部署 bit/HWH | BLOCKED；XSA 不能代替 PYNQ 部署包 |
| `pynq`及DMA驱动版本 | 未在目标镜像上读取 Python、`pynq`、内核和 AXI DMA 驱动版本 | BLOCKED |
| allocator/缓存语义 | 裸机固定 DDR 地址与显式缓存维护已存在，但它不证明 PYNQ allocator 的物理连续性、对齐、cache-line隔离、一致性或 flush/invalidate API | BLOCKED |
| Overlay 解析入口 | `pynq_probe.py`仍固定拒绝，未导入PYNQ、未解析HWH、未下载bit | NOT_RUN / BLOCKED |
| 真实S2MM/TLAST/停止 | 离线mock已覆盖所有权、缓存陈旧、短输出、超时和未静止释放；真实PYNQ DMA、TLAST、停止排空和恢复未执行 | NOT_RUN |

## 已完成但不能扩大解释的内容

- 新增 receive-only 静态 profile，可检查同构建身份、实际 AXI DMA 参数、
  外部 payload schema 哈希、TLAST/完成方式和停止语义。
- `pynq_probe.py`继续 fail-closed；未绕过准入门槛。
- 真实适配器API/状态机已经写成设计说明，但没有板端实现。

## 准入后可执行操作单

只有上表前五项都有可核对证据后，才由拓芙决定是否上板：

1. 在目标镜像启动后只读记录板卡、内核、Python、`pynq`和驱动版本；不下载overlay。
2. 从一次Vivado构建导出同名相邻bit/HWH，生成manifest并运行
   `validate_receive_profile.py`；不以合成示例代替。
3. 用 `Overlay(..., download=False)` 等该版本真实API只解析HWH，核对DMA、控制
   IP和中断清单；解析不一致立即停止。
4. 用最小一次性缓冲验证allocator地址/对齐/缓存API；没有明确释放与静止语义
   时不启动DMA。
5. 获得明确板端授权后，先做一包已知安全源S2MM接收，保存原始状态、实际长度、
   TLAST/完成证据、缓存事件及错误路径；任何超时/短输出保留缓冲，不盲目重试。

本报告不是实板操作授权，也不证明比赛 PYNQ 加分项已经完成。
