# Standards 独立复核

准确 SHA `94b5fe79d87e038e895878fb31030cded469bb33`，父提交 `a17c4acd7a61d8bc2b5b2e1944f8c40fa4cc9ebd`。

结论：**PASS_DATA_CROSSCHECK_ONLY**；本轴无阻断。仅批准八段四路诊断/开发输入的格式与可追溯归档，不批准精密角度、声学性能、真实加载身份或完整 M1/H3。

实际执行 `python -B check_independent.py`（本目录脚本，Python 3.12 及 NumPy）；完整输出 run02.log、逐段结果 result.json。它不导入作者解码/核验函数，不调用 F 盘工程入口。主代理另跑交付入口及离线测试。

- Git 父提交差异：286 个新增文件，全部位于本批目录；历史目录未修改。
- 当前清单 72 个文件 SHA256 全匹配；8 个当前目录，不使用误发 received-20260920-01。
- 8 × 288250 组、每段 9224000 字节：直接按 little-endian 8 word 解码；原 64 位 ID 连续，flags/reserved 为零、signed24 合法，metadata 首尾及样本计数准确。
- 对所有 BIN 字节独立重算 FNV1a32，与 UART 的样本/包数/字节数/FNV 匹配；每路最小、最大、零值计数与 UART 精确一致。
- CSV 全部 2306000 行逐整数比对 BIN，header、原 ID、4 通道、stream_error=0、空 error_flags 匹配。
- 32 份 WAV 格式均为 48 kHz 单声道 int16，全部样本精确等于 round-even(PCM24*12/256)，无新增削顶；原 PCM 没有因此改变。
- 8 份 dependencies 中共 48 个仓库文件引用与当前检出哈希一致；8 份 version-binding 对同一 preflight JSON 的哈希一致。未验证不可访问的 A 实际主机文件，也没有设备读回。

原始首次辅助失败 run01.log 保留：Git 默认对中文文件名转义，导致 B 辅助脚本范围断言失败。仅添加 `core.quotepath=false` 处理路径后以新日志重跑；该失败不是作者数据缺陷。没有篡改作者包。

语义边界：PUBLICATION 优先于 HANDOFF 编写时的“未推送”。当前 metadata 是操作者补充后状态，旧 version-binding 的 operator_loading_evidence=null 和早期 record null 均保留历史原貌；两者不构成设备身份读回。目标位置是目测中心参考约 1.5 m、操作者估计偏差 <= 5 cm；坐标/采样率/映射/隐藏手机 DSP 未经独立标定。背景暂停与鼠标点击来自后续声明，不能当绝对静音。各段独立 Run，编号不可拼接为连续会话。源文件不是阵列处同步干净参考。声学起止/混响不确定性未量化，标记与候选对齐不是评分标签。数据经调参后不再是独立验证集。

未执行：采集导出 process、ARM 编译、gate、下载、板测、仪器标定；不扩大旧批准。没有为代码气味提出与本批诊断无关的改写要求。
