# A 对 R1/R2 的增量独立复核

结论：通过限定复核，R1/R2 关闭。批准离线研究工具、结果归档和合同草案入库；不批准生产数制替换、正式声学性能、完整 H3、实板或实时。

## 身份和范围

- 准确远端待审提交：`fe67547635ff254f9f91c7f917e8dedb6daf3363`。
- 原版本：`bb964cbd5b4bee005702bebe6b9cee16d9b885d9`。
- 复用原报告：`5e343f2d9e9a372ad59bcc618571d4fb0002a7df:docs/reviews/b-checkpoint-bb964cb/REVIEW.md`。仅复用其中明确通过且未受影响的子项，不将旧 NEEDS_FIX 当批准。
- 合入前 main：`1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78`。
- B 相对 main 的全部变更限于 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/`；返修相对 bb964cb 为 28 个文件。相对实测提交 `0bea3461c1b7b0a9dfd4dcf509f4773ca10b1124`，最终提交没有 source 变更。
- 本轮复核比较器、反例、原字节准备、清单及新入口；不重新审查无关旧研究，不修改默认算法、冻结输入、旧失败、A/C 工程或公共阶段状态。

## 实际环境与执行

Windows，Intel Core i9-14900HX（实际查询），CPython 3.12.14、NumPy 2.3.5。独立 detached worktree 从准确 SHA 建立，共享工作区未切换或重置。

公开路径映射：`<SOURCE>` 为独立 Git 工作树，`<EXACT>` 为新原字节导出，`<OUT>` 为全新复现输出，`<PY312>` 为上述解释器；全部输出位于源工作树之外。完整原始输出在 A 本机保留，公开证据只作明确的路径占位符映射。

```powershell
# cwd=<SOURCE>
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/prepare_exact.py --repo . --commit fe67547635ff254f9f91c7f917e8dedb6daf3363 --out <EXACT>
# cwd=<EXACT>
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/verify.py
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/reproduce.py --out <OUT>
```

三条入口实际退出 0。导出 192 个文件；封闭清单 158 项、历史 21 文件、33 项依赖通过。入口依次运行 12 项新增测试、18 项原测试、study、golden，四个子进程均退出 0；运行前后冻结检查通过。脚本保留的 `AUTHOR_REPRODUCED_NOT_INDEPENDENT_APPROVAL` 是通用输出标签，不代表执行者身份；本报告记录 A 实际独立执行与裁决。

## 结果分层

| 检查 | A 实测 |
| --- | --- |
| JSON 语义 | 19/19 通过；仅显式 summary.environment 排除并记录两端环境 |
| JSON 文件字节 | 10 相同，9 不同（8 帧报告及研究 summary） |
| 浮点差异 | 2,261 处，最大绝对差 5.684341886080802e-14；均在字段容差内 |
| 离散结果、类型、状态、原因、输入哈希 | 严格一致 |
| WAV/PCM | 48/48 WAV 原字节一致，因此 PCM 相同 |
| 整数数组 | 120/120 键、dtype、shape、逐码一致 |
| golden 摘要 | 语义及字节一致，无浮点差异 |

R1：容差只用于列明的物理浮点字段，其他浮点仍精确；类型先行检查，有限值必检。角度绝对容差 1e-10 度；投影 1e-12 绝对/相对；功率 1e-6 绝对加 1e-12 相对。它们仅吸收数值舍入，不是声学准确度指标。检查了越界、NaN/Inf 双侧、状态/整数/键/类型/哈希篡改、未列浮点、PCM 及数组 dtype/shape/code 反例；均按预期拒绝。未改大阈值或冻结值来迁就本机。

R2：逐个 `git cat-file blob` 获取固定提交原字节，落盘再校验，依赖另对冻结清单严格校验；没有修改全局 Git 配置。CRLF 临时仓库反例验证工作副本不变，导出仍为原字节；已有输出拒绝，损坏和缺失诊断含路径及预期/实际哈希。192 文件导出实际成功，未复用旧输出。长路径旧失败、原 A 失败、原 golden01 失败均保留。

## 发现、复用与限制

无剩余 R1/R2 阻断。非阻断：本环境 JSON 字节与作者不完全相同，必须保留本表，不得改写为跨机器全部字节一致。比较规则只适用于当前固定 schema，未来添加字段时未列浮点仍应严格，不应扩大通配容差。

复用旧报告的独立 PCM 重算、研究方法/分母/合同审查及旧 run05/FFT 等未受影响结论，本轮未重做。算法源文件未改，未重新签发旧阶段验收。仍保留 reference25 默认路线；新 gate 数制、IP 映射、完整时延/缓存预算、目标身份、生产接入及硬件证据未获批准。旧日志 NOT_ARCHIVED 不关闭。

## 入库与收尾

批准范围为上述准确版本完整父包及 checkpoint 中已审离线研究材料，加本次 A 复核记录。候选继续以任务包为离线入口，不迁入生产活动算法；后续生产接入须有完整合同和对应验证。本轮不是正式阶段验收，不重写冻结阶段快照。

合并后按准确 Git 对象核对批准目录，并从最终路径执行新增反例 smoke test。完整复现原始文件保留于 A 独立证据目录；公开摘要、比较记录及路径映射命令见同目录 evidence/。不删旧失败或进行中分支。发布 SHA 与本地/远端对齐结果在最终回报中记录。

实际合并提交：`135f5a0c7d251846c90135f5acf49e8891f6ecc9`，非快进合并，无冲突。合并后 `git diff --exit-code fe67547635ff254f9f91c7f917e8dedb6daf3363 HEAD -- task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918` 退出 0；最终共享路径运行 `-B -m unittest discover -s task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source -p test_repair.py -v`，12 项通过、退出 0。

本批批准目录与 A 记录的 modified/staged/untracked/ignored 检查均无遗留（本条收尾记录提交前的自身修改除外）。其他任务的 continuous-*、A 候选及阶段操作单未跟踪材料原样保留，不属于本批未处理项。原始输出及原字节副本保留作为可追溯证据；未删除工作树、分支或旧失败。完整阶段收尾、生产接入及旧日志备份状态不由本次包级批准代替。
