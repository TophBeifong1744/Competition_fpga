# 9.18 完整定点合同与预算依赖：独立工作材料交回

**整理交付完成；生产格式和完整H3仍未冻结/未签通过。** 本目录仅为归档前工作区，原对话负责统一汇入既有任务包后交A完整复核，不另建同名任务包。

| 项 | 本次交回 |
|---|---|
| 任务/分工 | 执行 `F:/NUEC/validation/b-0918-followup/PARALLEL-HANDOFF.md` 定点合同收口；B侧材料整理，A负责IP/RTL/调度与独立裁决；声学回退诊断留给原对话 |
| 固定来源 | 只读 `F:/NUEC/review-worktrees/algorithm-closeout-20260923`；HEAD=`fe67547635ff254f9f91c7f917e8dedb6daf3363`；交接指定待审分支 `task/member-b-algorithm-closeout-20260923`，本次未核远端 |
| 表格入口 | [FIXED-CONTRACT.md](FIXED-CONTRACT.md)：Hann、gate去均值FFT、DOA FFT、29→25、功率门、互谱/PHAT、IFFT、lag/插值、DOA/置信度、DAS/饱和，含数制、出处、已有测试、缺项和下一步 |
| 预算入口 | [BUDGET-DEPENDENCIES.md](BUDGET-DEPENDENCIES.md)：8 FFT+6 IFFT依赖、操作量、缓存生命周期、待A裁决项；[budget.json](checks-02/budget.json)保留未知上界null |
| 增量计划 | [VALIDATION-PLAN.md](VALIDATION-PLAN.md)：B1–B6软件整数节点/边界、A1–A4 IP/RTL/调度/集成，全部标NOT_RUN；不改阈值、不加声学模拟或录音 |
| 本次变化 | 仅本目录新增文档、只读审计脚本及检查结果；未改变源算法/配置/冻结证据/默认reference25 |
| 准确依据 | [source-identities.json](checks-02/source-identities.json)记录204份唯一文件的Git blob及工作树SHA-256；[code-anchors.json](checks-02/code-anchors.json)记录函数/测试准确行号。依据涵盖交接指定文件、父数制/调度合同、PHAT、run05独立复核和AMD历史限定证据 |
| 实际执行 | CPython3.12.14/NumPy2.3.5；33项dependencies、158项snapshot条目、G-new八NPZ共120数组的键/dtype/shape/原始码字节哈希一致；工作树与所查blob无差异；预算算术103364周期/107496B；源树前后status均空 |
| 检查限制 | 这是身份/完整性/算术检查，未重新计算FFT或golden，未运行候选测试/八段/run05/耐久/声学诊断；没有新RTL仿真、综合实现、实板、WCET测量。旧测试仅引用，作者自检不代签 |
| 首次失败 | [checks-01/FAILURE.md](checks-01/FAILURE.md)：Git所有权保护导致启动失败。仅进程级safe.directory准确路径及GIT_OPTIONAL_LOCKS=0后在checks-02成功，不改全局配置、不覆盖失败目录 |
| 剩余阻断 | 生产profile与AMD映射、全幅/保护/内部字宽、新gate统一整数链、DAS延迟码、实际调度/资源/存储/背压/CDC/输出均待补证，详见增量计划。`103364`不等于WCET，`107496B`不等于实际资源或完整内存上界 |
| 写入/发布状态 | 仅写本目录；未改只读源树、原交接目录、其他任务包、主流程状态或one；未提交、推送、合main，未向A发送消息。实际检查时间见result.json（UTC），不从文件名倒填9/23日期 |

## 关键结论

- 保留默认reference25。portable Q30与AMD24位twiddle逐码证据分开，固定右移4只是一条候选。
- gate先去均值再加窗；DOA未去均值。窗与逐级量化使两者不能未经证明复用数值结果，当前最坏按8+6变换计。
- 峰值margin是诊断字段，不是已生效置信度拒绝阈值；DOA几何一致不证明目标存在。`speech_present/target_identity`保持unknown。
- 新gate存在独有边界缺口；DAS角到delay仍含浮点sin/cos。旧软件断流限定PASS与本次八探针都不能扩展成全链生产冻结。

## 本次只读检查复现

只重做身份及预算算术，不调用旧研究/仿真入口。输出必须是本目录内不存在的新子目录：

```powershell
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'F:/NUEC/validation/b-0918-fixed-contract-work/audit.py' --out 'F:/NUEC/validation/b-0918-fixed-contract-work/checks-next'
```

本轮成功输出：[result.json](checks-02/result.json)、[frozen-array-checks.json](checks-02/frozen-array-checks.json)。脚本不导入源模型、不写源树，读取准确commit原blob；拒绝源HEAD改变和越界输出。JSON里的PASS仅指列出的只读检查，不是A复核结论。

交付末检由 `check_delivery.py` 核对文档链接、预算null、源HEAD/status；结果为 `delivery-check.json`，独立工作材料哈希清单为 `WORK-SHA256.json`（仅封存本目录，不改源清单）。

原对话归档时请保留本页限定结论、来源身份和首错，引用旧证据唯一原件；将此处材料汇入既有包后，按最终提交更新入口及做相称链接/身份检查。本工作区没有可供发布的提交号。
