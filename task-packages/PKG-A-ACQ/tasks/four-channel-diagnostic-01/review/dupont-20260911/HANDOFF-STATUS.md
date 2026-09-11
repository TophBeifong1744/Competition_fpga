# 四路诊断交接状态

2026-09-11。A侧交接前复核通过；B本人尚未收到通知或提交独立诊断回执。待拓芙转交下列ZIP及B-HANDOFF.md。本机无可直接连接的B本人任务，不将“原理问题”或“A承接B外包”任务冒充成员B。

## 已准备

- 完整包：[soundsight-four-dupont-diagnostic-20260911.zip](handoff/soundsight-four-dupont-diagnostic-20260911.zip)
- B操作/复核提示：[B-HANDOFF.md](B-HANDOFF.md)
- A结论与边界：[REVIEW.md](REVIEW.md)
- ZIP字节数：3,797,025；SHA-256：`a5d9bb8388d0921c53d254340030ae0b584111d7381b8a2d88a5c49079324721`。
- ZIP内71份负载文件及1份清单。包含原BIN、串口、H1 CSV/metadata、8份试听WAV、当前构建证据、原读取器及测试、复核源码和通过/失败记录。来源路径在build-snapshot/manifest.json中保留；不是可直接搬走运行的完整Vivado工程。

## 新位置验证

在打包后的副本目录实际运行verify_manifest.py，71份哈希通过；audit_capture.py两段逐值/串口复算通过；audit_listening.py八WAV逐点通过；47+8+9项软件回归再次通过。记录在portable-check01/；这是A侧便携性检查，不是B独立复核。ZIP再核对CRC及全部声明SHA通过。

原始数据未修改，未重建/重载硬件，未修改B算法、RTL或Vitis应用；只新增复核/交接材料并更新当前进度。全工作区diff检查发现原有dfx_runtime.txt尾空格，未触碰无关文件；本轮修改范围另行检查。

## 仍待

1. 拓芙把ZIP和提示转交B；B直接解析并给独立通道诊断回执，不等长稳、实测坐标或C板实物。
2. B回执后主流程按范围记录H2四路诊断交接；正式M1、DOA、波束、H3和C板实物不自动通过。
3. 当前未提交、推送或合并。原始BIN/日志/WAV/ZIP受Git忽略规则影响，后续若授权Git发布，必须明确纳入它们并在隔离发布范围内处理，不可只上传CSV。阶段最终批准尚未发生，因此不改9月10日冻结快照、不提前作9月16日阶段关闭；正式收尾再执行docs/phase-closeout.md。
