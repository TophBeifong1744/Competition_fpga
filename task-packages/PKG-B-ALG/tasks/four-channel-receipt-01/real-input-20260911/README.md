# 首批真实四路输入登记

登记日期：2026-09-11。**A 原交付已获 B 可接收回执；本目录新增 B 登记、证据迁移与复跑适配仍待 A 复核。** 本次只做身份核对与收尾登记，不重复数值诊断，不新增验收结论。

## 固定输入与状态

| 对象 | 身份 / 状态 |
| --- | --- |
| 已批准诊断入口 | PR #9，main `e811c399adaa083d520bfda998f15fe86b445b9a`，A 限定复核通过 |
| A 原实录 | `d088e2c7deda9c505c094fd48d6f90bcd7f52807` |
| A 交付加 B 回执 | `2e2f685faf5520181cdd00cde2cd5030e75e67e2`，分支 `codex/toph/four-channel-dupont-diagnostic-01` |
| 当前远端检查 | 2026-09-11 fetch 成功；main 仍为 `e811c39`，原交付及回执尚未合入；非持续监控结果 |
| 本登记分支 | `task/member-b-real-input-register-01`，从上述 main 独立建立 |

固定远端原件：[B-REVIEW](https://github.com/TophBeifong1744/Competition_fpga/blob/2e2f685faf5520181cdd00cde2cd5030e75e67e2/task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/B-REVIEW.md)、[B-START](https://github.com/TophBeifong1744/Competition_fpga/blob/2e2f685faf5520181cdd00cde2cd5030e75e67e2/task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/B-START.md)。B-START 的“回执尚待”和 B-REVIEW 末尾“未提交”是各自撰写时状态，由 `2e2f685` 发布的回执和本登记补充当前状态，不改原件。

两段独立 acquisition 均四路、32000 组、原始 BIN 各 1024000 字节；配置 48 kHz 下各约 0.667 秒，不拼接时间轴。quiet ID 为 17544..49543，speech 为 15798..47797。来源是操作者声明的杜邦线四只麦，有 BIN/串口日志相符支持；软件不能认证物理映射。几何 coordinates_m 未测。

[REGISTER.json](REGISTER.json) 固定输入提交、回执 Git blob/SHA-256、各 capture 文件哈希、历史证据哈希及本机来源。负载清单 SHA-256 为 `6c1505533787558a204fa4ed303931b4006e7519c2416f632a4ec32bbf003c01`；全部 76 个原发布文件身份见 [08-independent.json](historical-evidence/08-independent.json)。本次从成功 fetch 的 Git 对象再次核对这 76 项及回执身份，不再依赖当时的下载 API 响应才能确认来源。

## 已有结果与未完成项

历史 B 回执完成清单、原始 BIN/串口/CSV、编号、幅值、相关与频谱检查；71 项负载清单及 64 项软件回归通过（47 读取器、8 导出、9 门禁）。本次没有重跑这些回归，不能把历史日志算为本轮测试。

无本轮阻断。低频共同成分、mic2 高频差异、高相关配对仍为非阻断跟踪项；不据此判定供电故障、坏麦或复制通道。后续由 A 按既有硬件安排记录 mic0..3 物理对应及几何，再做局部声学激励和条件对照，B 据新增输入继续分析，不新增本轮交付门槛。

未完成 / 未批准：实测几何和采样时钟、声学同步与标定、长期稳定、正式 M1、完整 H2、定位精度、波束/增强收益、H3、C 转接板实物和完整板级验收。定点工作仍沿原任务推进。

## 证据共享与复跑

- `historical-evidence/` 是从 `F:/NUEC/review-evidence/a-dupont-d088e2c/` 原字节复制的 10 个小型日志、JSON 和原脚本。原脚本有历史绝对路径，仅存档，不直接执行。
- 原始大文件继续引用 A 固定提交，不在 B 包重复保存 BIN/CSV/WAV/ZIP/bit/XSA/ELF。API 响应、失败下载、原本机 `b-recheck-01` 完整输出仍仅在本机，未宣称它们已发布。
- `verify_register.py` 验证迁移哈希、76 项 Git 身份、回执更新没有改变原输入、回执身份和登记索引；只需 Python 与 Git。见 [VALIDATION.md](VALIDATION.md)。
- `replay_independent.py` 沿用历史数值计算，仅将绝对路径/API树依赖替换为 `--delivery` 和已有 76 项哈希，使用新的输出文件。需要 Python 3.12 / NumPy；本轮只验证语法及与原计算部分一致，未重新执行数值诊断，也未赋予其独立批准地位。

复跑由复核人需要时执行，不是重新要求完整交付：

```powershell
# 在含本登记的仓库根目录；先 fetch 原交付分支以取得固定 Git 对象。
git fetch origin codex/toph/four-channel-dupont-diagnostic-01
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/verify_register.py
# 如需要数值复跑，先确认以下新路径不存在，再创建固定输入的独立只读用途 worktree。
git worktree add --detach ../a-dupont-replay-new d088e2c7deda9c505c094fd48d6f90bcd7f52807
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/replay_independent.py --delivery ../a-dupont-replay-new/task-packages/PKG-A-ACQ/deliveries/dupont-diagnostic-20260911 --output ../b-independent-replay-new.json
```

新输出可与历史 `08-independent.json` 按 JSON 对象比较；环境差异可能影响浮点末位。A 包完整复跑命令仍按固定 B-REVIEW 第 2 节执行，工作目录应为 A 交付的 `payload/`，不能误用外层回执所在目录。不要覆盖历史输出。

## 收尾与合入职责

见 [HANDOFF.md](HANDOFF.md) 和 [PR-BODY.md](PR-BODY.md)。本阶段无新增获准源码；本目录为诊断存档与登记，适合留在任务包，不强搬入算法活动目录。既有 PR #9 入口的后续归位由主流程在阶段批准范围内按 `docs/phase-closeout.md` 处理，本次不扩展集成范围。新增材料待 A 复核，尚不构成阶段收尾全部完成，也未写入已验收阶段快照。后续阶段归档由主流程保存对应 CLOSEOUT 与准确发布 SHA；本登记提交可由本文件 Git 历史定位。
