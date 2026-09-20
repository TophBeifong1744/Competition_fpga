# 八段四路开发输入：待审发布入口

2026-09-20；仅申请B独立格式/声学诊断，不申请M1/H3、精密方向或音频收益验收。作者材料见 HANDOFF-20260920.md；README和准备期清单为历史，不覆盖后续操作确认。

## 当前数据与复现

八段唯一入口由 evidence/background-confirmation-20260920-01/CURRENT-DATA-SHA256.json 的72项当前数据哈希界定。其中8份metadata对应8个采集目录；received-20260920-01是用户误发的历史证据，不属于有效八段，不证明硬件故障。首次原件、旧清单和元数据备份全部保留。目测角度、用户估计5cm偏差、手机隐藏DSP未知、鼠标点击及活动边界不确定性均保持原说明。

从仓库根运行（Python需NumPy，输出目录必须不存在）：

```powershell
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918/scripts/verify_delivery.py --out ../eight-captures-b-review-new
python -B -m unittest discover -s task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918/scripts -p test_offline.py
```

verify_delivery按当前清单验哈希并对八段分别调用仓库B读取器，不使用历史绝对路径；命令和输出保存在新目录。原process_capture.py的process入口还会校验A机器F盘实际工程，不能称为B机器无需硬件环境的可移植导出入口。本次未重跑该导出过程，也未改其保护逻辑；B可直接读取交付BIN/CSV并独立诊断。

## 工作执行实际检查

独立发布副本当前72项哈希无差异，8/8读取器PASS_FORMAT_ONLY，10项离线测试通过。证据见 evidence/publication-check-20260920/。未重新上板、构建、重算精确声学标签、标定或完成B独立诊断。源WAV声明哈希为ce28c5576eea620d8f358c0799bf8029cdc41bdeae8dcf95a02967d3bace6838。

发布仅新增本目录，其他任务不夹带；使用局部-text属性保持原始字节，不修改旧清单。当前结论PASS_PUBLICATION_FORMAT_ONLY，不是独立验收。该开发数据经调参后不得作为独立留出集；源WAV也不是阵列处同步干净参考。无需继续录制，先等待B针对实际材料给出诊断。
