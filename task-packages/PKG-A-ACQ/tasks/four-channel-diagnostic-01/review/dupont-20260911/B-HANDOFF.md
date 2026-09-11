# 发给 B：杜邦线四路首批实录独立诊断

请以成员B身份接收并独立诊断本包，先核对MANIFEST.sha256.json，再在独立的新输出目录复跑，保留所有原始输入和失败记录。

本次是实际杜邦线连接的4只麦，不是C转接板实物；大致共面、约40mm正方形，安静与人声两次间未移动。坐标未测，metadata保持null。声源方向/距离未知。配置名称虽含c-adapter，仅指固件接口，不代表用了转接板。配置`ss-data-draft-0.3`不变，原始编号、signed24/int32和错误标志不改。

## 输入与A已做的事

- captures/dupont-quiet-01 与 captures/dupont-speech-01：每段原始BIN、完整串口、metadata.json和samples.csv，各32000组四路、1024000字节、约0.667秒。
- captures/listening-01：8个共同增益12的PCM16试听副本及转换说明，禁止当原始H1数据。拓芙已试听，反馈人声清晰；非B独立试听结论。
- REVIEW.md、run02/：A侧BIN/UART/CSV逐值及哈希复算通过，读取器PASS_FORMAT_ONLY；64项软件回归通过。run01保留审核脚本首次错按UTF-8读取UTF-16日志的失败，不是采集失败。
- build-snapshot/：当前one/c_adapter_platform/four_mic_capture产物及源码。ELF构建Sep 11 2026 18:23:59；bit=37f6d55f…，XSA=71e7bf6d…，ELF=c0b430e7…，完整SHA见清单。不套用build06哈希。

## 解压后直接运行

在解压出的包根目录执行；使用已安装NumPy的Python。新输出目录不能已存在：

```powershell
python -B verify_manifest.py .
python -B b-reader/payload/model/python/h1_reader.py captures/dupont-quiet-01 captures/dupont-speech-01
python -B audit_capture.py --captures captures --reader b-reader/payload/model/python/h1_reader.py --output b-recheck-01
python -B audit_listening.py --captures captures --output b-recheck-01/listening.json
python -B b-reader/payload/tb/python/test_h1_reader.py
python -B source/test_export.py
python -B source/test_c_capture_gate.py
```

包内b-reader/reference的code-pattern/restart只是47项读取器测试的合成夹具；真实诊断入口只能用上述dupont两段。不要调用source/export_c_capture.py的C板实物导出命令重新标记本次杜邦线输入；本包已提供匹配的真实metadata，无需重新导出。

## 请完成并回传

1. 独立报告格式/哈希、编号连续区间、丢样/重启/错误、各路幅值、均值、RMS、饱和；区分未报告错误与所有物理故障均不存在。
2. 查恒定、完全重复、异常相似、偏置及其他通道异常；必要时比较安静/人声相关性或频谱。相关性不单独证明物理映射或同步标定通过；不要从未知坐标求角度。
3. 试听可用于通道诊断，保留共同增益说明；不把不同片段的幅度差叫作SNR改善。
4. 在自己的任务目录留下输入ZIP或清单SHA、读取器版本、实际命令、结果和明确回执：“可接收／需修改；当前观察；下一处排查建议”。不改原数据、补通道、拼接跨次编号或替换默认算法。

范围只有四麦真实输入诊断，不是六麦定位、DOA精度、波束收益、正式M1、H3或C转接板实物验收。先诊断这两段，不等一小时长稳或完整场景库；算法/定点/H3材料照常并行。B反馈回来后主流程再判断H2四路诊断交接是否关闭；本包未宣称B已收到、未提交推送或合入。
