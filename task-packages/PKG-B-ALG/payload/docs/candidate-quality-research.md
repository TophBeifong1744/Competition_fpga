# 原定位候选质量研究：部分白化GCC

开发版本candidate-quality-0.1。保留原PHAT定位、已验证的5/12捕获和所有旧批次；新算法为独立weighted_gcc.py，不改变默认入口。当前只完成浮点合成研究，没有H3或硬件批准。

## 本轮改了哪一处

原GCC对每对麦克风的互谱Z执行PHAT：Z/max(|Z|,1e-15)。研究变体执行Z/max(|Z|,1e-15)^β，β为0.75或0.5；β越接近1越接近原PHAT。β<1保留部分幅度信息，检验是否能减轻弱频点相位噪声对相关峰的影响。

仅改这一指数。仍用同一1024点Hann窗、300–4000 Hz频带、2%幅度掩码、至少12频点、物理时差范围及0.05点余量、三点抛物线插值。15对时差仍交原最小二乘求解，范数[0.7,1.3]、残差≤0.5点、有限对数/秩要求均不变。没有利用真值、允许圆锥或跟踪历史去选GCC峰。

原始候选和变体候选都接相同的QuorumSession(5,12,120 ms)。因此可以分别比较原定位候选质量，以及在相同捕获器下的最终新有效输出，避免同时修改两个环节。

β=1测试逐项等于旧GCC，覆盖原9场景×3方向。两个候选均通过六轴/斜向符号、静音、公共增益缩放、非法输入、溢出、输入不被修改及真值隔离测试。β=1的一致性证明未引入其他数值算法变化，不等于新β在所有声学条件下更优。

## 开发和验证如何分开

协议在开发评价前保存于payload/config/candidate-quality-protocol.json：开发种子2026091000–2026091009，验证种子2026091100–2026091109，均未在之前捕获研究使用。5个场景、时间表与标注定义沿用固定batch-presence计划。

预先只比较β=0.75和0.5。判据要求：噪声下原始候选与捕获后≤10°正确率分别比同批旧候选提高至少5个百分点；两层新有效P95均≤12°；各场景捕获后不在场误输出率增幅≤0.5个百分点；正常场景两层正确率下降≤1个百分点；噪声两层>30°错误率增幅≤0.5个百分点。若两者通过，按预先约定优先较小改动β=0.75，不按开发集最大收益临时选β=0.5。

开发集两者均通过，所以冻结β=0.75。selection.json保存选定配置、协议与全部参与源文件哈希。验证只运行此候选，入口拒绝选择后的代码/协议变化；看到验证结果后未改参。协议的负结果后备分支（两候选均失败时只验证β=0.75作为未获推荐假设）本轮未触发。

这仍是相同合成分布的新随机实现，不是跨真实环境泛化。协议没有将“同锥竞争者的≤10°正确率不退步”列为通过条件，因此该项即使下降仍可能通过协议；报告必须单列这种局限，不把判据通过理解为全场景胜出。

## 如何复现

```powershell
cd F:\NUEC\task-packages\PKG-B-ALG
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/candidate_quality_research.py --phase develop --out evidence/my-candidate-development
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B payload/model/python/candidate_quality_research.py --phase validate --selection evidence/my-candidate-development/selection.json --out evidence/my-candidate-validation
```

目录须不存在。开发/验证各运行50个试验、23350个声学帧。开发共6种方法，140100行；验证共4种方法，93400行。original_raw是原候选；original_quorum是原候选+相同5/12；gcc_beta075_raw/quorum是对应变体。HOLD不计新有效，过渡帧仍驱动状态但不混入在场/不在场稳态分母。

结果包括frames.csv、per-seed.csv、pooled.json/csv、paired.csv、latencies.csv、gates.json、inputs.json、run.json；开发另有selection.json。配对差均在同种子同帧定义下计算；正确率以全部在场帧为分母，P95仅以新有效在场帧计算，未定义值为JSON null/CSV空白。

candidate-diagnostics.csv在每个候选层记录有限对数、原始范数、残差、拒绝原因、原算法valid，以及对理论目标到达时差的误差。理论时差由同一1.5m球面几何计算，只有完整在场帧才有定义；时差RMS仅覆盖该帧有限的麦克风对，不能把缺失对当成零误差。该诊断真值在候选计算后使用，不参与估计。

独立审计脚本从固定的candidate-development-01和candidate-heldout-01目录复算标注、角度、质量门、HOLD排除、500组逐种子统计、50组汇总、配对增益及延迟，并核验选定代码、源文件和未重叠种子：

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B audit_candidate_quality.py --out evidence/my-candidate-audit.json
```

新输出路径须不存在。它还把116750条候选诊断与原始输出行逐项对应；时差真值RMS由实验代码计算，审计汇总其分布，没有从保存的波形重算全部相关函数。完整回归仍使用run_validation.py指定新目录。

## 当前结果与后续边界

新种子噪声下，β=0.75原候选有效率58.235%，相同5/12后的新有效率53.945%、≤10°正确率50.727%、新有效P95 10.232°。详细同批对照见evidence/candidate-quality-report.md。10个新种子均有正确率改善，但约一半在场帧仍无新有效输出。

同锥竞争者的≤10°正确率有所下降，目标不发声时身份错误输出率仍为97.546%；等强范围外竞争源仍未产生捕获。正常场景原始候选出现1个新增的不在场输出，但5/12层没有新误输出。不得宣称这是全场景替代方案。

当前没有自然语音、实测房间响应、硬件/定点代价或实时性能结论；分数指数仍是浮点运算。后续应先限定该候选适用范围，并使用新噪声类型、方向或混响条件检验副作用，不继续用本次验证种子调参。完整包仍由A明确复核后负责合入。
