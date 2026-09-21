# H3-E-01～03 增量返修待审发布

实际日期2026-09-21，工作执行检查，不是B技术批准。

| 项目 | 内容 |
| --- | --- |
| 受审基线 | 0abdc91c57787b7c868a797b88f35129de169faf；本分支直接从该提交延续 |
| B反馈 | 02f4ec23d771bd33a04ae3f297178ca34d537eb8，docs/reviews/a-h3-two-20260921/ |
| 分支 | codex/toph/h3-engineering-repair-20260921；新准确SHA以本发布提交为准 |
| 申请范围 | 独立Python工程状态模型及复现入口返修；三项问题由B增量裁决 |
| 实现入口 | repair-h3-e01-e03/README.md、source/results.py、source/prepare.py、source/run_checks.py |
| 原件保护 | 不改原0ab源码/清单、B反馈、f879逻辑包、fbbaa16待审C包或实际工程 |
| 原清单 | repair-h3-e01-e03/SHA256.json，422项，SHA-256为130cf067ca2dcbe21ff3ad3a70fc2d92881bc0aa3948b6d6c4d3dc25988aa6c5 |
| 集成边界 | 暂留研究任务包；不接入生产，不冻结ABI，不替换C候选，不宣称H3或实时通过 |

## 本轮复跑

使用本分支隔离副本中的原字节prepare.py，从固定0ab/f879/02f对象导出；在仓库外运行导出副本run_checks.py，10组回归、0失败、0错误。原缺陷复现与修复结果分开，详见publication-repair-evidence/regression-run/。未重跑无关FFT、数值或耐久。

附加check_entry.py检查使用共享目录较短路径的同字节源码：已有输出拒绝、空对象库拒绝、原工程/C候选保护。该原件保护检查需要两包工作文件，**它是发布保护审计，不是独立导出回归的运行依赖**。干净检出的核心复现按作者README执行prepare和导出的run_checks即可；共享保护项只在有原工作文件的副本运行，不能因没有C包而声称核心返修无法复现。

## 失败与环境边界

- 首次沙箱账户调用Git因dubious ownership退出128，未进入测试；以仓库所有者身份重跑，未修改全局safe.directory。
- 发布检查器首次目录集合比较包含了作者seal明确排除的临时.git/description；按同一封包规则排除后检查422项一致。该临时Git内部元数据在本地保留，不作为任务源文件提交；失败文字证据仍在作者历史目录。
- 深路径副本的check_entry.py发生ModuleNotFoundError: prepare，未进入负例；改用已核对同字节的较短原路径，独立输出entry02。该限制保留，不称原深路径命令通过。异机建议短检出路径，输出必须新建。

具体命令、stdout/stderr及入口结果在publication-repair-evidence/，原作者证据与422项清单未重封存。发布复跑输出为新增证据，不计入原清单。

ARM/BSP、AMD仿真、RTL、CDC、实板未执行；REALTIME_BLOCKED。最终是否关闭E01/E02/E03由B独立复核决定。未合入main，其他工作不清理。
