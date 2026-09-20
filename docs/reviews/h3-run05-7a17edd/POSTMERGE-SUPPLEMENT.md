# B 合入后核验补充回执（用户转交，2026-09-20）

来源：用户在本项目会话转交的B核验摘要。下面技术运行结果由B报告，本轮A只核对版本/原件身份并补文档，未重跑技术测试。B所列两份原始文件位于B电脑，本机不可访问，本文不是其原文副本，也未声称独立核过两份文件的哈希。

- B核验时远端main：`6751664d18db077046e0a5d5a0bfc84fcefce108`；合入提交：`a440d9bb67a42d9f666370bbaed2cbbf252f77d1`。
- 受审候选：`7a17edd2b5408e10608d954f3e7fa11cb62fe34b`，已是main祖先；69个任务包blob、18项输入与受审版本一致。
- B报告提交`7b25d51ce82de432ead1984fb95e53bd8ab19c8a`不是必须合入的祖先；其报告以相同blob `6d5e16b24be041da01f48c4383a99430025c034c`、8993字节进入main，不能因未合整条反馈分支误判报告丢失。
- B在Python 3.12.14 / NumPy 2.3.5下核验：包清单退出0、18项输入退出0、39项测试通过、run05冻结14数组及事件精确一致，数值/字节差异为0。
- 首次误用Python 3.7造成环境失败；切换规定环境后通过。该失败保留为环境历史，不判为合入回归。

B原始记录由B保管：

- `F:/NUEC/review-evidence/h3-main-6751664-postmerge-minimal-01/POSTMERGE-VERIFY.md`
- `F:/NUEC/review-evidence/h3-main-6751664-postmerge-minimal-01/frozen-run05-check-3.12.json`

## 更新裁决

**维持LIMITED PASS：run05软件断流闭环的合入后技术核验通过。** Spec为0项问题；不签完整H3，也不扩大到实板、实时、正式方向、音频收益或真实PYNQ。

B补交时Standards指出2项文档流程缺口、1项非阻断判断项。本轮处理：

1. `CLOSEOUT.md`已补B核验主线SHA、合入提交与结果摘要；准确命令、cwd及部分进程退出码尚缺，**记录缺口未完全关闭**，逐项见下表。
2. 原始首错日志已核实950字节、只读和SHA-256；[取回说明](RAW-LOG-RETRIEVAL.md)已补准确失败命令。但第二个可恢复副本和访问控制尚未验证，状态为 **NOT_ARCHIVED**，不宣称归档缺口已关闭；B实际取回尚未发生。
3. 裸字典/字符串状态可考虑dataclass/Enum，保留为非阻断后续判断，不在本次文档补交中重构。

A本轮文档核对基线为`8755ccc57b72dd6392c592705ed1e9b0e7523187`：候选祖先关系退出0，任务包69项相对候选无路径变化，B报告blob保持一致。`6751664`是B核验时点，不应回写成此后永久不变的“当前远端”。本次文档发布的最终SHA由Git历史及发布回报定位。

## c7fb2eb之后的最后文档补记

本轮基于`c7fb2ebc62ada32b45a81a8225314072c19581c9`，仅补文档。以下不填造B未提供的命令，也不拿A曾运行的类似命令代替B实际命令。

| B核验步骤 | 准确命令 | cwd | 输出目录/文件 | 进程退出码及来源 |
| --- | --- | --- | --- | --- |
| 首轮Python3.7 | NOT_PROVIDED | NOT_PROVIDED | 单项日志路径NOT_PROVIDED | NOT_RECORDED；B只报告环境失败 |
| Python3.12包清单检查 | NOT_PROVIDED | NOT_PROVIDED | B总证据目录见下文，具体日志名未提供 | 0，来自用户转交B摘要 |
| 18项输入检查 | NOT_PROVIDED | NOT_PROVIDED | B总证据目录，具体日志名未提供 | 0，来自用户转交B摘要 |
| 39项单元测试 | NOT_PROVIDED | NOT_PROVIDED | B总证据目录，具体日志名未提供 | NOT_RECORDED；39项全过为B报告，摘要未逐项给进程数值 |
| run05冻结比较 | NOT_PROVIDED | NOT_PROVIDED | `frozen-run05-check-3.12.json` | NOT_RECORDED；14数组/事件精确一致为B报告 |

B总输出目录准确为`F:/NUEC/review-evidence/h3-main-6751664-postmerge-minimal-01/`。其`POSTMERGE-VERIFY.md`与结果JSON本机均不可读取；该目录是**输出目录，不能据此猜测cwd**。补齐方式是由B提供现成原始核验记录/命令回执，含实际解释器、完整参数、cwd、逐项日志路径及数值退出码，无须重测。当前这些字段是明确待补信息，不是本轮新增技术阻断；LIMITED PASS保持。

## c7fb2eb发布核对回执

上一轮文档发布实际三端均为`c7fb2ebc62ada32b45a81a8225314072c19581c9`；本轮开始再次直接查询得到相同结果。命令cwd为`E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga`。

| 查询命令 | 结果 | 退出码 |
| --- | --- | --- |
| `git rev-parse main` | `c7fb2ebc62ada32b45a81a8225314072c19581c9` | 0 |
| `git rev-parse origin/main` | `c7fb2ebc62ada32b45a81a8225314072c19581c9` | 0 |
| `git ls-remote --heads origin main` | `c7fb2ebc62ada32b45a81a8225314072c19581c9 refs/heads/main` | 0 |
| `git rev-list --left-right --count main...origin/main` | `0 0`（ahead=0，behind=0） | 0 |

这张表固定记录c7fb2eb发布及本次补录前的身份；本轮新文档提交发布后另在交付回报给准确三端SHA，不将自引用占位符伪装成已经发生的核对。
