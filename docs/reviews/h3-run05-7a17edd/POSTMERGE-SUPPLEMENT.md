# B 合入后核验补充回执（用户转交，2026-09-20）

来源：用户在本项目会话转交的B核验摘要及后续命令补充回执。下面技术运行结果由B报告，A未重跑技术测试；公开文档用路径占位符，准确个人路径只留在B私下原件。本页按B补充回执纠正执行环境归属，不把摘要错误继续当事实。

- B核验时远端main：`6751664d18db077046e0a5d5a0bfc84fcefce108`；合入提交：`a440d9bb67a42d9f666370bbaed2cbbf252f77d1`。
- 受审候选：`7a17edd2b5408e10608d954f3e7fa11cb62fe34b`，已是main祖先；69个任务包blob、18项输入与受审版本一致。
- B报告提交`7b25d51ce82de432ead1984fb95e53bd8ab19c8a`不是必须合入的祖先；其报告以相同blob `6d5e16b24be041da01f48c4383a99430025c034c`、8993字节进入main，不能因未合整条反馈分支误判报告丢失。
- 默认Python 3.7.0 / NumPy 1.21.6下，包清单和18项输入检查分别退出0；39项测试退出1并报13项环境错误，run05冻结检查因缺少`math.isqrt`退出1。
- 切换Python 3.12.14 / NumPy 2.3.5后，只重跑39项测试与run05冻结检查，二者均退出0；14数组及事件精确一致，数值/字节差异为0。3.7失败保留为环境历史，不判为合入回归。

B原始记录由B保管，个人绝对路径不进入Git：

- `B-POSTMERGE-VERIFY-6751664`：`POSTMERGE-VERIFY.md`，2495字节，SHA-256 `DE5221C4AC776ACEA9933305C8A159E90C36DEFB21A1CC4407293730ED3162F7`。
- `B-FROZEN-RUN05-CHECK-3.12`：`frozen-run05-check-3.12.json`，6781字节，SHA-256 `6C98C6E8502E42DD43B32DF5AE6B4946F1E3A197A943B4B8EABEE2FBAE436FB3`。
- `B-POSTMERGE-COMMAND-ADDENDUM`：命令补充回执，6003字节，SHA-256 `930A57BAA4AAC8189EED532DDD147F17960261ECF979457A0A5A10207292F5E4`。本页的执行矩阵以该回执为准；它纠正前一份摘要对Python环境的合并表述。

## 更新裁决

**维持LIMITED PASS：run05软件断流闭环的合入后技术核验通过。** Spec为0项问题；不签完整H3，也不扩大到实板、实时、正式方向、音频收益或真实PYNQ。

B补交时Standards指出2项文档流程缺口、1项非阻断判断项。本轮处理：

1. `CLOSEOUT.md`已补B核验主线SHA、合入提交与结果摘要；B后续提供了经路径脱敏的准确命令、cwd映射、输出身份及进程退出码，逐项见下表。
2. 原始首错日志已核实950字节、只读和SHA-256；[取回说明](RAW-LOG-RETRIEVAL.md)已补准确失败命令。但第二个可恢复副本和访问控制尚未验证，状态为 **NOT_ARCHIVED**，不宣称归档缺口已关闭；B实际取回尚未发生。
3. 裸字典/字符串状态可考虑dataclass/Enum，保留为非阻断后续判断，不在本次文档补交中重构。

A本轮文档核对基线为`8755ccc57b72dd6392c592705ed1e9b0e7523187`：候选祖先关系退出0，任务包69项相对候选无路径变化，B报告blob保持一致。`6751664`是B核验时点，不应回写成此后永久不变的“当前远端”。本次文档发布的最终SHA由Git历史及发布回报定位。

## B合后核验准确执行矩阵

本节来自`B-POSTMERGE-COMMAND-ADDENDUM`，没有重跑。路径映射为：`<B_REPO_ROOT>`是B对准确`7a17edd2b5408e10608d954f3e7fa11cb62fe34b`的API归档检出根；`<B_PACKAGE>`是其下`task-packages/PKG-B-ALG/tasks/h3-complete-20260918`；`<B_OUT>`是B的任务包外新输出目录；`<B_PY312>`是B的Codex缓存Python 3.12解释器。私下回执保留映射原值，公开Git不记录个人工作区。

所有命令cwd均为`<B_REPO_ROOT>`；stdout/stderr由执行工具返回，除结果JSON外没有写独立本地日志。

| B核验步骤 | 路径规范化后的准确命令 | 输出 | 进程退出码 |
| --- | --- | --- | --- |
| 默认环境 | `python --version`及`python -c "import numpy; print(numpy.__version__)"` | Python 3.7.0 / NumPy 1.21.6 | 0 |
| 包清单 | `python -B <B_PACKAGE>/source/seal_package.py --package <B_PACKAGE> --verify` | `PACKAGE MANIFEST PASS: files=68` | 0 |
| 18项输入 | `python -B <B_PACKAGE>/source/seal_inputs.py --repo <B_REPO_ROOT> --out <B_PACKAGE>/inputs.json --verify` | `PASS_INPUT_GIT_BLOB_HASHES 18 CRLF_NORMALIZED 0` | 0 |
| 3.7下39项测试 | `python -B -m unittest discover -s <B_PACKAGE>/tests -v` | 39项中13项环境错误；无本地日志文件 | 1 |
| 3.7下冻结检查 | `python -B <B_PACKAGE>/source/check_golden.py --repo <B_REPO_ROOT> --golden <B_PACKAGE>/evidence/run05/golden/golden-stages.npz --out <B_OUT>/frozen-run05-check.json` | 缺少`math.isqrt`，目标JSON未形成 | 1 |
| 规定环境 | `<B_PY312> --version`及`<B_PY312> -c "import numpy; print(numpy.__version__)"` | Python 3.12.14 / NumPy 2.3.5 | 0 |
| 3.12下39项测试 | `<B_PY312> -B -m unittest discover -s <B_PACKAGE>/tests -v` | `Ran 39 tests`、`OK`；无本地日志文件 | 0 |
| 3.12下冻结检查 | `<B_PY312> -B <B_PACKAGE>/source/check_golden.py --repo <B_REPO_ROOT> --golden <B_PACKAGE>/evidence/run05/golden/golden-stages.npz --out <B_OUT>/frozen-run05-check-3.12.json` | 6781字节结果JSON；`PASS_ALL_FROZEN_STAGES_AND_EVENTS_EXACT 14` | 0 |

本次没有运行README的完整单命令，也没有重跑三路音频、真实诊断、预算或Skill检查；不得把它们写成本轮合后最小复现结果。上述纠正不改变任务包/输入字节身份、39项测试结果、14组冻结比较或LIMITED PASS范围。

## c7fb2eb发布核对回执

上一轮文档发布实际三端均为`c7fb2ebc62ada32b45a81a8225314072c19581c9`；本轮开始再次直接查询得到相同结果。命令cwd为`<A_REPO_ROOT>`，准确个人路径不进入Git。A未保留准确核查时间，只能绑定在`aa2b07d`发布前的作者记录，不能用提交时间冒充命令执行时间。

| 查询命令 | 结果 | 退出码 |
| --- | --- | --- |
| `git rev-parse main` | `c7fb2ebc62ada32b45a81a8225314072c19581c9` | 0 |
| `git rev-parse origin/main` | `c7fb2ebc62ada32b45a81a8225314072c19581c9` | 0 |
| `git ls-remote --heads origin main` | `c7fb2ebc62ada32b45a81a8225314072c19581c9 refs/heads/main` | 0 |
| `git rev-list --left-right --count main...origin/main` | `0 0`（ahead=0，behind=0） | 0 |

这张表固定记录c7fb2eb发布及本次补录前的身份；本轮新文档提交发布后另在交付回报给准确三端SHA，不将自引用占位符伪装成已经发生的核对。

该作者回执没有记录当时工作树的modified/staged/untracked/ignored分类计数、未处理数及逐项处置，状态保持`NOT_RECORDED`，不由B推测补齐。B于2026-09-20 20:07:27（UTC+8）另以GitHub API只读确认远端main为`aa2b07dca9ffc91a421cee592807270ef05cd3fe`，并确认`c7fb2eb...aa2b07d`仅含1个文档提交、5个文档路径；这不等于对A本地工作树的独立核对。
