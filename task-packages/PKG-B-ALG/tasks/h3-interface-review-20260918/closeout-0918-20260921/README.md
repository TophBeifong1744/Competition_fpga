# 9.18 遗留任务：声学诊断与定点合同集中收口

实际整理日期2026-09-21。**两条工作线的本轮材料已集中，不代表9.18声学基线或完整H3通过。** 当前申请离线诊断、负结果、合同/预算整理入库；不替换默认reference25、PHAT、Tracker或生产profile。

## 准确版本及已批准范围

- 新分支基线 main：`e55f0d520b654380d0cacd642f2fb45cad767640`，新任务分支 `task/member-b-0918-consolidation-01`；复用现有工作树，没有额外复制Git工程。
- 两条工作线共同来源：`fe67547635ff254f9f91c7f917e8dedb6daf3363`。
- A 已对该版本 R1/R2 限定通过，合并提交 `135f5a0c7d251846c90135f5acf49e8891f6ecc9`。报告见仓库 `docs/reviews/b-checkpoint-fe67547/REVIEW.md`。不再将R1/R2列为待修。
- A Intel：19 JSON语义通过，10份字节一致/9份不同；2261处浮点差异最大5.684341886080802e-14；离散/输入哈希严格一致、48 WAV字节一致、120整数数组一致。本机全字节一致不能替代此跨环境描述。
- 本次复制的两份工作目录保留原件、原哈希和当时状态，因此其中“待A复核”“尚未提交”等是历史时点，当前状态以本页和准确发布回执为准。原脚本中的F盘工作路径也作为历史命令保留，不伪装成可移植发布入口。

## 一次阅读入口

| 工作线 | 成果入口 | 本轮结论 |
|---|---|---|
| 回退诊断 | [连续帧报告](acoustic/PAIR-DIAGNOSIS.md) | 重放13464跟踪状态；137捕获帧及相邻共320帧/1920对复算，27次捕获重启伴随峰变化；原跟踪规则不满足，物理根因未唯一确定 |
| 联合候选 | [负结果](acoustic/JOINT-STUDY.md) | 八段仍0 fresh，捕获137→120；新增218数值放行全为原低范数帧，199落网格下界；本轮不采用 |
| 定点合同 | [统一逐级表](fixed/FIXED-CONTRACT.md) | Hann、去均值gate、FFT/PHAT/IFFT/lag/DOA/DAS规则与出处齐；生产数制、内部字宽、完整新gate整数流仍待验证 |
| 算力/缓存 | [预算及生命周期](fixed/BUDGET-DEPENDENCIES.md) | 新gate与DOA不自动复用变换：8 FFT+6 IFFT；103364周期仅历史槽算术，107496B仅列举项，实际WCET/内存上界null |
| 后续动作 | [统一剩余任务](REMAINING.md)及[详细B1–B6/A1–A4计划](fixed/VALIDATION-PLAN.md) | 当前是计划，不能累计成已通过测试 |

## 已执行、复用、尚未执行

- 已执行诊断：冻结状态重放；320帧PHAT相关复算；298帧符号/镜像代数不变性；一种固定联合候选全八段开发对照；4项数学/控制反例；4488帧配对边界分析。没有重生成WAV、没有新录音或四麦声学模拟。
- 定点对话已执行：33依赖、158原snapshot条目及120冻结数组的身份检查，204唯一来源绑定，预算算术；未运行新整数链。首个Git所有权失败和后续成功记录原样保留。
- 本次集中检查只验证搬迁完整性、旧文件未改、204来源Git对象、预算null/算术，并在新路径跑4项联合候选测试与4488帧已有产物配对后处理；不重跑旧FFT/run05/音频/耐久。
- 未执行：B1–B6新边界验证、A新IP/RTL对照、资源时序、实板、真实声学精度/音频收益、完整H3及实时准入。没有读取或代签A共享未提交工程。

## 可移植复核入口

Python3.12、NumPy2.3.5、Git；从本分支仓库根目录执行，输出为仓库外不存在的新目录：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/closeout-0918-20260921/check_closeout.py --out ../b-0918-consolidation-check-new
```

Windows普通检出如发生字节差异，不改全局Git配置或清单。沿已批准原字节导出器准备准确本次提交：

```powershell
$reviewSha = '<本次发布的完整SHA>'
$sourceRepo = (Get-Location).Path
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/prepare_exact.py --repo . --commit $reviewSha --out ../b-0918-consolidation-exact-new
if ($LASTEXITCODE -ne 0) { throw '准备失败，保留输出' }
Push-Location ../b-0918-consolidation-exact-new
try {
  python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/closeout-0918-20260921/check_closeout.py --git-repo $sourceRepo --out ../b-0918-consolidation-check-new
  if ($LASTEXITCODE -ne 0) { throw '检查失败，保留日志' }
} finally { Pop-Location }
```

`--git-repo`只读取准确fe67547历史对象，允许在无.git的原字节导出内运行检查。无需执行fixed/audit.py里绑定原工作树HEAD的历史命令，也不要求A复建作者F盘目录。

封存：旧158条快照原件在SNAPSHOT-before-consolidation.json，两份工作目录清单原样保留。仅扩充父包当前checkpoint/SNAPSHOT-SHA256.json以包含本次增量，不改其158个旧条目对应文件。没有更改冻结PCM/JSON/整数golden或旧失败。复核通过后由A或获授权工作执行按范围合入，B不自审自合。

## 本次集中检查回执

[validation/check01/result.json](validation/check01/result.json)：原158文件未改、两份34/13项封存材料一致、204份Git来源匹配、预算算术/null保持；新路径4项测试和4488帧配对后处理通过。检查时集合211项，随后仅加入本回执、复核提示词和日志封存，不改变被测代码。命令与stdout/stderr在同目录。作者集中检查不是A独立批准。
