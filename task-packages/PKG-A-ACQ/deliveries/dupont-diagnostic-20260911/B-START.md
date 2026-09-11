# 给 B 的本次发布提示

请独立接收A的四路杜邦线真实诊断录音，不复用此前合成/接口夹具结论。

- 分支：`codex/toph/four-channel-dupont-diagnostic-01`。
- 包目录：`task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/`。
- 先确认远端分支确实有本目录并记录实际SHA，在独立副本检查，不覆盖你当前工作。
- 读本目录README.md及payload/REVIEW.md，再按payload/B-HANDOFF.md复跑；完整的原始数据在payload/captures中，不能只取CSV。

在本目录payload下执行（Python需NumPy）：

```powershell
python -B verify_manifest.py .
python -B b-reader/payload/model/python/h1_reader.py captures/dupont-quiet-01 captures/dupont-speech-01
python -B audit_capture.py --captures captures --reader b-reader/payload/model/python/h1_reader.py --output b-recheck-01
python -B audit_listening.py --captures captures --output b-recheck-01/listening.json
```

实际为杜邦线四只麦，大致共面约40mm正方形，两次未移动但坐标未测，metadata为null。每段32000组约0.667秒。当前ELF为Sep 11 2026 18:23:59，匹配bit/XSA的SHA在包中，不用build06旧哈希。拓芙已试听人声清晰；WAV是统一增益12的副本，不是原始H1或降噪收益证据。

请回传输入提交SHA/清单、独立执行命令、可解析性、编号/错误/连续区间、每路幅值/偏置/RMS/饱和及重复通道检查、必要的相关性/频谱诊断，并明确“可接收／需修改”和下一处排查建议。没有测量坐标，不求定位精度；不补六路、不改原始编号、不用试听响度当SNR改善。

本次仍是diagnostic，B独立回执尚待；不宣称正式M1、H3、定位、波束或C板实物通过，不自行合入main。你的定点/H3工作不因此停工。
