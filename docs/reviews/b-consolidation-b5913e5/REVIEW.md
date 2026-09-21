# A 增量独立复核：9.18 遗留材料集中收口

结论：**通过限定复核**。仅批准离线回退诊断、联合候选负结果、定点合同与预算整理入库。不是完整 H3、正式声学收益、生产 profile、实板或实时批准。

## 准确身份及范围

- 直接远端查询固定分支 `task/member-b-0918-consolidation-01` 为 `b5913e596e28b30f9e04cf2c9ba365430b8914df`；不是按移动分支审批。
- main 基线 `e55f0d520b654380d0cacd642f2fb45cad767640`。
- 仅新增 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/closeout-0918-20260921/` 61 文件及父 `checkpoint-20260923/SNAPSHOT-SHA256.json` 增量，共 62 文件。
- 旧 snapshot 与 fe67547 Git blob 原字节相同；原 158 项文件未改。默认 reference25、PHAT、Tracker、冻结音频及 A/C 工程未改。
- R1/R2 复用 `docs/reviews/b-checkpoint-fe67547/REVIEW.md` 的限定通过，不重新派修。19 JSON 语义通过而 9 份字节不同的 Intel 结论正确保留。

## 实际执行（2026-09-21）

Windows，CPython 3.12.14 / NumPy 2.3.5；使用准确提交的 Git blob 导出独立目录，不切换或重置共享 checkout，不改全局 Git 配置。`<SOURCE>` 是原 Git 仓库，`<EXACT>` 是新外部导出目录，`<OUT>` 是全新外部检查目录。

```powershell
# cwd=<SOURCE>
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/prepare_exact.py --repo . --commit b5913e596e28b30f9e04cf2c9ba365430b8914df --out <EXACT>
# cwd=<EXACT>
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/closeout-0918-20260921/check_closeout.py --git-repo <SOURCE> --out <OUT>
# cwd=<SOURCE>，A 独立后处理，不运行 FFT
<PY312> -B docs/reviews/b-consolidation-b5913e5/audit_existing.py <EXACT> <SOURCE> <OUT>/a-independent.json
```

以上退出码均为 0。原字节导出 253 文件；当前封存 219 项、原 158 项、声学 34/定点 13 项封存检查通过；204 项历史 Git 来源通过。四项联合候选反例通过；4488 帧配对后处理通过。没有重跑 FFT、八段音频生成、run05、耐久或新定点边界实现。实际 stdout/stderr 和公开摘要见 evidence/；原始命令日志留在 A 新外部目录，公开命令采用上述占位符。

## 逐项裁决

1. **声学归因通过。** 独立从冻结逐帧数据核对 787 活动放行帧：不足对81、仅残差326、仅范数39、两者26、通过315，分母闭合。137 捕获帧及相邻去重320帧/1920对均有绑定证据；捕获组777有效对、39少频点、6越界。27次重启的逐帧角距及相邻整数峰变化复算相符。这是全录音的机制诊断，包含背景/标记，报告未冒充正式准确率，也未唯一归咎混响或校准。
2. **联合负结果通过。** 4488帧中双方有效2182、双方拒绝1667、原有效新拒绝421、原拒绝新有效218；活动门内损失57、增加32。捕获137→120；joint_gated、joint_ungated均0 fresh。218新增放行全为原范数<0.1，其中199落半径0.1边界。源码是在约束网格内选择，不等价于原自由拟合后范数拒绝；文档明确指出且本轮不采用，未将网格边界当质量证据。
3. **定点合同整理通过。** 逐级表区分PCM码单位和归一化F、Python容器和硬件宽度；抽核 integer_gate 的均值/窗/移位/功率/状态及 PHAT 的epsilon、mask、开方/倒数与来源相符。120冻结数组的dtype/shape描述与原NPZ相符，NPZ原字节受未改snapshot保护；没有新增逐码算法批准。portable Q30与AMD24位twiddle分列，DOA/DAS及内部宽度缺口保留。B1–B6/A1–A4明确NOT_RUN。
4. **预算身份通过。** 8FFT+6IFFT、8×7366+6×7406=103364周期、列举缓存107496B计算相符；真实WCET、实际内存、资源、端到端延迟和停顿上界仍null。合同说明gate去均值窗与DOA不自动共用结果，串行工作区共享也不等于变换复用；没有把历史槽或列举缓存当完整上界。
5. **范围/历史通过。** 原失败记录、历史来源与R1/R2批准边界保留；复制工作材料中的历史“未提交/待A”等已由当前README明确解释，不作为当前状态。没有新增M1或摄像头入库门槛。

## 发现与限制

无本轮阻断或必须返修项。非阻断注意：`check_closeout.py` 的四测试/4488帧结果只覆盖本轮身份、算术和后处理；不能当作重新运行了13464状态重放、320帧PHAT或新的完整整数链。本轮A另行核对既有逐帧证据和27次重启，未重算FFT；这一区别必须保留。

历史槽、软件合同、开发集0 fresh及约束下新放行都不构成生产/性能准入。后续B按已列B1+B3优先做整数边界，A按现有资料核对几何/通道与工程映射；这些是后续任务，不阻断本次材料入库。旧日志备份/完整H3等未由本轮关闭。

## 发布收尾边界

仅合入上述固定新增目录与增量封存，以及本A审核记录。保持任务包内离线入口，不迁入默认生产算法；原因是本次候选不采用、合同/预算仍未冻结。本轮不是正式阶段验收，不重写阶段公共状态或冻结快照。发布后准确合并SHA、main三端对齐及本批材料分类另行回报；其他未完成任务原样保留。

实际非快进合并 `0aec8d72d9227803b479249f9a470b9de2e2129e`，无冲突。合后批准父目录相对准确 b5913e5 的 `git diff --exit-code` 为0；最终共享路径运行 `-B -m unittest discover -s task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/closeout-0918-20260921/acoustic -p test_joint.py -v`，4项通过、退出0，不重复全套检查。

本批 modified/staged/untracked/ignored 检查无未处理项（本条收尾记录提交前自身除外）；原字节导出和原始执行日志有明确外部留存，公开关键结果已提交。其他任务的 continuous-*、A 候选和阶段操作单未跟踪资料原样保留。未删除任何分支、旧失败或工作资料；作者后续任务完成性未确认，不擅自清理其分支。最终 main SHA 与三端对齐以发布回报为准。
