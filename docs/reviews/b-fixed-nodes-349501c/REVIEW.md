# A 独立复核：固定数值节点

结论：**通过限定复核**。仅批准离线节点测试、独立保护候选、数制及接口修订建议入库；默认算法/阈值、生产接口、完整 H3、AMD/RTL/实时/实板均未获批准。

## 版本、依赖及范围

- 开始首先执行 `git rev-parse HEAD`：`5570ad7a3957994e6915d3ef9706303445c02efa`。
- 直接远端查询待审分支 `task/member-b-fixed-nodes-01`：`349501c560f7f9d195ebbf52a4c47f34695bfeae`；后续均按该准确提交检查。
- 依赖 `b5913e596e28b30f9e04cf2c9ba365430b8914df` 已由 A 上一轮单独限定复核，合并 `0aec8d72d9227803b479249f9a470b9de2e2129e`，发布 main `5570ad7...`。本轮引用 `docs/reviews/b-consolidation-b5913e5/REVIEW.md`，不是自动批准依赖。B 入口“依赖尚未合入”是交付时点状态，已被此独立记录更新。
- 相对依赖仅新增 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/fixed-nodes-20260921/` 及父 checkpoint 快照增量，共89文件。与当前 main 的树差异显示缺少 A 前轮报告，是分支基线先后关系，不作为删除授权；合并须保留 A 已发布报告。
- 原219条文件未改，`SNAPSHOT-before-nodes.json` 与 b5913e5 原 snapshot Git blob 字节完全相同；新307条封闭清单通过。没有覆写历史消除差异。

## 实际运行

Windows / CPython3.12.14 / NumPy2.3.5。从准确提交导出341文件原字节副本至新外部目录；未切换、重置共享 checkout，未改 B 实现。

```powershell
# cwd=<SOURCE>；<EXACT>/<OUT> 均为全新外部目录
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/prepare_exact.py --repo . --commit 349501c560f7f9d195ebbf52a4c47f34695bfeae --out <EXACT>
# cwd=<EXACT>
<PY312> -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/fixed-nodes-20260921/run_all.py --repo . --out <OUT>
# cwd=<SOURCE>
<PY312> -B docs/reviews/b-fixed-nodes-349501c/independent.py <EXACT> <SOURCE> <OUT>/a-independent-run02.json
```

原字节准备退出0；三组节点检查各退出0，总入口退出0。A补充检查最终退出0；其首次动态导入遗漏导致的启动失败和修复记录见 A-HARNESS-FAILURE.md，不算 B 失败或通过用例。原始运行目录保留，公开日志/摘要见 evidence/，命令用路径占位符而非个人绝对路径。

| 组 | 本次A实跑 |
| --- | --- |
| B1/B3 | 13前端、7功率、4096状态序列/24840步、66阈值用例；12非法调用严格候选均拒绝、原入口7类接受缺口仍记录；6功率入口拒绝；八份Hann身份一致 |
| B2/B4 | 33适配值、32蝶形/4溢出分量、26开方、256倒数表项、207非零归一化（实际理想差0码、预定界2码）；mask、补谱、上游故障及6次IFFT错误汇总检查通过 |
| B5/B6 | 56 lag、12物理边界、252数值DOA、36阈值guard、656顶点；18有效数量级CORDIC；6 DAS及16固定延迟跨块对照通过 |
| A补充 | 自建方形坐标与Fraction消元独立复算656顶点；另12组全幅整数夹具逐次输出前缀及最终PCM对独立Fraction插值一致，8种非法延迟/PCM拒绝，final后再次push拒绝 |

## 关键裁决

1. **原节点与oracle分离成立。** 前端/功率、蝶形、DOA阈值、IFFT汇总从绑定原源码AST提取，仅暴露节点/替换返回；原舍入函数在DUT侧。Fraction/Decimal期待值不调用DUT舍入/开方；完整FFT调用设禁止。Hann只是与既有golden身份比较，不冒充独立cos/ROM证明。状态oracle独立按比例和序列计算。
2. **非法输入不被放宽。** 类型、范围、形状、非有限值、配置等反例维持拒绝；严格候选未偷偷修原入口。既有7类输入缺口及3类通用补谱缺口仍保留。FrameGuard仅单事务软件建议，未证明真实status/TLAST/跨session握手，晚错不可撤回已提交样点。
3. **S23F20建议成立但限定几何。** A独立复算全部656合法时延盒顶点，拒绝前ux/uy最大绝对码2531477，8顶点超S22且原宽整数模型全部拒绝。每固定有效对集的线性LS分量及单调RNE使盒顶点可界定分量；需至少S23容纳后再判拒绝。它不证明乘积/分母/CORDIC全中间字宽，不覆盖新几何/非法tau，不冻结生产格式。
4. **StreamDAS最终PCM与时刻必须分开。** 原16组固定延迟对照及A另12组前缀/最终PCM一致。候选最大lookahead=9样点，不能自动替代旧8样点接口；即使零延迟也保守等待1样点。缓存还受chunk大小影响。原单块函数直接分块159点差异仅是数学夹具，不是实录断音；候选未覆盖动态切向、HOLD/TTL、多bank、reset、ready服务。
5. **CORDIC缺口未扩大解释。** 极小轴向向量出现2530个Q8角码偏差，现有范数门排除该数量级；不能称已接受实录方向错误。18个正常数量级样例不是所有允许向量的误差证明，通用归一化/保护仍待验证。

## 阻断、未测、批准边界

本轮材料入库无阻断；生产接入仍需明确S23及9样点接口决策、全中间位宽、动态DAS和真实完成协议证据。本轮不改生产接口或默认reference25/PHAT/Tracker/阈值，不运行AMD/RTL/实板/整链实时，不重跑旧声学/FFT/run05/耐久研究。旧失败及R1/R2限定批准结论复用，不倒签完整H3。

仅按准确新增范围及增量snapshot合入；新候选继续在任务包作为研究入口，未迁入生产活动目录。本轮非正式阶段验收，不更新公共阶段状态。其他成员未提交资料和旧失败保留；本批发布/相称验证和三端核对另行记录。
