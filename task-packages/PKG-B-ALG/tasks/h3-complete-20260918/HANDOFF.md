# HANDOFF：A → B（9/18 四路 H3 返修候选）

本次仅申请软件候选及缺口材料的独立复核，**不申请完整 H3 PASS，不自行合入 main**。

## 固定版本

- 仓库：`TophBeifong1744/Competition_fpga`。
- 主线父提交：`5cfa02e51af44bb5c930babf732ddc864a1ab6cd`，包含 `21780c3`。
- B 退回的返修父提交：`be3a2ed20d123a37bf79650f3d6a1685fc5d8625`。
- 新的源码/冻结证据提交：`74306d036ae329a687f24ab8d153c3e2f4375189`。
- 交付分支：`task/member-a-0918-h3-closeout`。B 应在复核时以 `git rev-parse HEAD`、`git rev-parse origin/task/member-a-0918-h3-closeout`、`git ls-remote origin refs/heads/task/member-a-0918-h3-closeout` 三者相同的**最终提交**为准；源码提交号不代替最终审查 SHA。
- 范围：`task-packages/PKG-B-ALG/tasks/h3-complete-20260918/` 和 `deliverables/phase-2026-09-18/README.md`；默认 PHAT、原 Tracker、录音、RTL/BD/XDC/Vitis、Skill 活动源码未改。

## 返修变化与复核点

1. `inputs.json` 的18项字节数和哈希改为准确提交的 Git blob；本机仅允许 CRLF→LF 与 blob 精确相同。复现前后各验一次；作者复跑均为18项PASS，其中2项工作区 CRLF 归一化。
2. run04 冻结14组整数数组，并单独冻结/对比窗口/FFT/IFFT标志、6 pair lag、DOA、Tracker状态/事件、断流、音频时序和边界向量。独立检查器不把重算出的结果伪作原冻结值。作者37项测试、14数组和全部冻结事件PASS；请B独立变异或复算验证。
3. 自动路用对应帧末才得出的方向：五帧前单麦回退，首个 fresh 在样点3072算出、3080可用、3081有首个非零波束权重；后续19°切换、70°拒绝、HOLD到期/回退、断流和480样点淡变。19°与70°是注入控制反例，不是声学定位成绩；`manual != automatic` 的测试阻断旧回填错误。
4. lag 合法边界改为边/对角专属整数 Q12 判定；正负边界内、边界上、边界外有测试，不再由 `math.hypot` 或浮点比较生成物理边界。
5. 原 run03 的单个含个人绝对路径作者复现记录经拓芙批准移出当前树，仓库外只读原件与旧提交 `be3a2ed` 可恢复，原 SHA 和脱敏摘要见 `evidence/run04/PRIVACY-AND-HISTORY.md`。run01方向符号首错、run02秩不足覆盖问题和run03其余证据保留。

## B 的单命令复现

在最终准确 SHA 的干净独立检出仓库根目录运行，要求 Python 3.12 + NumPy 2.3.5，输出目录先不存在：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/reproduce.py --repo . --out ../h3-review-new-run
```

入口先验包清单和18项输入，运行37项新测试、逐级golden复算、真实输入诊断、预算/Skill检查、原批准三路音频50项检查，最后再次验18项输入。作者复现状态仅为 `PASS_AUTHOR_REPRODUCTION_NOT_INDEPENDENT_REVIEW`。

## 保持的限制

- center与quiet的存在门均为61/61过门；quiet fresh=0是后级扇区/跟踪所致，不是存在门拒绝背景。
- 待审六秒S1录音 `8f708e42caf32c1de6f30726298e3edf0e1970b6` 未复制、未批准，不产生正式真值指标。
- 73900周期只是两个历史OOC测试槽的算术相加，91080B只是保守缓存清单，不是整链实测或BRAM映射。
- SKL-001仅模块仿真限定；SKL-002仅offline static/mock；真实PYNQ、实板音频、AMD全链bit-exact、完整RTL/时序、P50/P95及客观音频收益均未准入或NOT_RUN。

建议B最多裁决“可复现的四路H3软件候选材料限定准入”，完整H3保持 `NEEDS_MORE_EVIDENCE`。阻断问题先退回A，不合入main。
