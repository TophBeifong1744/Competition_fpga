# B 修复候选独立复核（2026-09-14）

本记录由 B 独立运行后签署，批准只绑定下列准确 Git SHA 和目录。作者自检与历史代理评估没有直接转为批准；旧反馈仍固定在 `review/member-b-skills-20260914` 的 `0ef0355642ea8719d5e4cdde0a38c531550218d4`，原文、源码快照和日志均保留。

## SKL-002：PASS（限定离线实现）

- 准确批准 SHA：`3ac597d1d16982e0a5c5a114202ca8568dc28d8f`；仅 `skill/pynq-overlay-dma-validation/`。审批的是 static/mock 工具、文档及证据，真实 PYNQ 尚未准入。
- 原候选 `55039cf8bfab2bd6112192c8bd646d427a52a642` 的 D1/D2/D3 均关闭。本次没有修改作者实现；合入后该目录须与候选逐 Git blob 相同。
- 独立工作树 `F:/NUEC/review-worktrees/b-skl002-3ac597d`，起始干净 detached HEAD；本机 Windows，Python `D:/Python/python.exe` 3.13.0。测试输出新建，未覆盖作者 evidence。
- 证据唯一发布入口：[本轮证据](../../results/skill-review/b-rereview-20260914/)，SHA-256/字节清单 `manifest-skl002.json`；原始 CLI 命令、cwd、退出码与 stdout/stderr 分别保存在每次运行子目录。

| 原问题 | 独立结论与证据 |
| --- | --- |
| D1 HWH 合同实例绑定 | 复用 B 原 thermal/missing-dma-ip.json、missing-control-ip.json 原字节，经新 CLI 均退出 1、FAIL、HWH_CONTRACT_IP。端口 NAME、参数 NAME、MODULENAME、完整层级的尾段不能冒充 MODULE 实例；合法完整层级路径及带前导斜线路径通过。变体 HWH 与 manifest 重新配套哈希，避免用哈希错误代替实例检查。见 d-independent/ 相应输入、command.json、result.json 与日志。 |
| D2 同 ID 覆盖失败 | 原 duplicate-evidence.json 经新 CLI 退出 1、FAIL、DMA_RUN_DUPLICATE。坏→好、好→坏、好→好、坏→坏、好→坏→好均失败；合法唯一 ID 正常证据通过。逐条拒绝重复，不允许后条覆写掩盖失败。 |
| D3 独立分发说明 | README 明示原创/第三方来源、MIT 边界、路径大小写映射及项目导出规则链接；LICENSE.txt 与仓库根 MIT 署名及全文逐字节一致。不替 AMD/IP、板厂、PYNQ 等授权；仅批准导出方案说明，未验收最终竞赛导出包。 |

实际命令（前三条 cwd 为准确候选的 Skill 目录）：

```text
D:/Python/python.exe -B scripts/run_offline_tests.py --output results/b-rereview-tests-new.json
D:/Python/python.exe -B scripts/simulate_dma.py --contract references/example-session.json --output results/b-rereview-receive-new.json
D:/Python/python.exe -B scripts/simulate_dma.py --contract references/example-session.json --fault timeout --fault abort-timeout --output results/b-rereview-timeout-new.json
D:/Python/python.exe -B F:/NUEC/review-evidence/skills-b-rereview-20260914/independent_d.py F:/NUEC/review-worktrees/b-skl002-3ac597d/skill/pynq-overlay-dma-validation
F:/STUDY/IT/Anaconda3/python.exe -X utf8 -B C:/Users/BryanZheng/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/pynq-overlay-dma-validation
```

独立运行结果：55 个测试方法、57 个 subtest，0 failure/error/skip；正常模拟退出 0，96 bytes 与 golden 精确一致。双超时退出 1、FAIL、retained、session_blocked，trace 无 rx.read/rx.release，属于预期负例，不是回归失败。`independent_d.py` 的 60 项检查全部通过（包含原输入字节核对，不能说成 60 个新测试方法）；thermal signed16/96 bytes、pixel uint32/128 bytes 各 7 个会话，共 14 次，同一核心复用。

会话包含正常、缓存陈旧、部分启动后停止失败、状态读取失败、双超时、短输出、释放失败；失败后再次调用不增加 adapter 操作，未确认静止时不读/不释放，释放异常不重复释放。独立检查 2**120 的一整数差、明确容差、浮点溢出边界及短输出。board guard 退出 2、BOARD_RUNNER_NOT_QUALIFIED，未创建报告或接触板卡。现有测试同时覆盖失效状态、缓存所有权、停止/重复释放和下一轮阻断。

结构验证使用已有 Python 3.7.0/PyYAML 3.13，quick_validate 返回 Skill is valid；Python 3.13 环境缺 PyYAML，没有安装依赖。结构验证不替代行为测试。

`repair-manifest.json` 全部 105 项与准确提交 Git blob、工作树字节及字节数一致，旧 manifest 和旧日志没有改写。旧反馈输入亦逐字节复用。真实工程仍为 simple S2MM-only，无 MM2S/DRE，不因合成 loopback profile 的通过虚构身份寄存器、PYNQ 镜像或实板能力；模拟时钟数据不是硬件吞吐或加速收益。

## 共用未测边界与发布约束

真实 PYNQ/Overlay/物理 DMA、综合资源/时序、CDC、板测、整机、最终竞赛导出、10 月 1 日 Skill 总验收：全部 NOT_RUN。本次没有采购、烧板、修改生产 RTL/BD/XDC，也未改变 B 的 9 月 18 日算法主线或 H1/H2/H3，没有给 C 新增任务。限定实现批准不保证比赛固定加分。

候选分支在合入前再次直接核实准确 SHA；main 从执行时远端最新版本接入，不回退历史版本。维护入口及本复核记录由 B 随限定合入更新，作者实现和历史证据原字节保留。发布 SHA 和合入后验证在后续发布核对中补记。

A 共享 main 的 162 项旧候选混合差异位于 A 电脑，B 未处理、未代签清理或同步。A 需在本机先保留/比对独有材料，再安全同步 main、核对已修改/未跟踪/忽略项；不要求 reset 脏目录。仓库中有报告不等于成员已收到消息，本次未用工具通知 A/C。

SKL-002 合入后验证：在真实本地 main 工作树的活动 Skill 目录再次运行全部离线测试，55 方法/57 subtest、0 failure/error/skip；源码路径与候选 Git blob 一致。实际命令与日志见证据 skl002-postmerge-units/ 及 skl002-postmerge-tests.json。原脚本报告中的 AUTHOR_SELF_TEST_NOT_B_ACCEPTANCE 为固定模板字段，B 本次批准仅由本签署记录给出，未改原始报告。
