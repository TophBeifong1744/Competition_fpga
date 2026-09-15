# 给 A 的复核提示词

请复核 Competition_fpga 分支 `task/member-b-real-audio-compare-01`，准确SHA使用B本次推送回报。基线 `09ecf267813e1ac289dae9358d9e097a87906c86`，包为 `task-packages/PKG-B-ALG/tasks/real-audio-compare-01`。

申请范围：四路冻结实录的单麦/手动指向离线音频对照源码及证据入库。不申请完整H3、自动指向、定点DAS、实时连续性、定位精度或降噪收益通过。没有修改默认算法、冻结实录、旧复核或主流程状态。

请先读README，再用Python 3.12及NumPy（作者2.3.5）在仓库根运行：

```powershell
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
python -B "$pkg/verify_delivery.py"
python -B -m unittest discover -s $pkg -p test_render_audio.py -v
python -B "$pkg/check_inputs.py" --out "$pkg/evidence/a-input-check01.json"
python -B "$pkg/render_audio.py" --out "$pkg/evidence/a-audio-run01"
```

每条检查退出码0，新输出不能覆盖原证据。比对新旧result中的裁剪区间、补偿符号、音频长度、峰值、量化误差及饱和计数，并对WAV解码数值检查；文件字节不同与数值差异分开记录，不只比较总数。作者已有8项延迟/边界/PCM测试通过，两段各31992配对样本，8个WAV均回读整数码一致、无饱和。原适配/分帧24项测试在步骤1通过。

重点：四麦实际几何，正补偿定义output_i[n]=input_i[n-delay_i]；共同有效区间，无环绕/填零/跨错误拼接；单麦mic0，四路等权平均；原标度与64倍统一试听增益分开；24位RNE与饱和。线性插值有频率衰减，−45°只是预先选择的试验方向，不是相对mic1约10cm位置的阵列中心真值。

用户听过所呈现的短人声对照，反馈“差不多清楚，无发闷失真断音爆音”，绑定文件见listening-01.json；播放设备、背景变化未提供，不推断收益。quiet主观试听未确认。未做完整流式/动态跟踪/RTL/实板/跨CPU验证，详见README。

通过后由你按准确范围合入并验证。本次入口保留本任务包作为离线诊断，不迁入默认算法。完整批准且确认无独有内容后，可清理此短期分支与B工作树 `F:/NUEC/review-worktrees/member-b-real-audio-compare-01`；其他任务及原始证据不动。请回传准确审核SHA、实际命令/结果、差异与批准范围。
