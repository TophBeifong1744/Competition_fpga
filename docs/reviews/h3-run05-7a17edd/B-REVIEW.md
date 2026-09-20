# 成员 B 增量独立复核：四路 H3 断流闭环 run05

- 复核日期：2026-09-20（Asia/Shanghai）
- 仓库：`TophBeifong1744/Competition_fpga`
- 分支：`task/member-a-0918-h3-closeout`
- 实际审核 SHA：`7a17edd2b5408e10608d954f3e7fa11cb62fe34b`
- 提交 tree：`db6e4274a6b40f10fa8eca5316f1c2d84e10f2fe`
- 增量固定点：`7ea3de519c1f86832fcb03fc8d852606273a8f8a`
- 裁决：`LIMITED PASS — run05 软件断流闭环增量限定通过`
- 发布：未合入 `main`；不签完整 H3 PASS。

## 1. 远端身份与增量范围

GitHub 远端 ref 已现场确认精确指向 `7a17edd2b5408e10608d954f3e7fa11cb62fe34b`。相对上一轮退回 SHA：

- merge-base 正是 `7ea3de519c1f86832fcb03fc8d852606273a8f8a`；
- ahead 2、behind 0；
- 提交为 `cef9c61 fix(h3): route gap reset into causal automatic audio` 和 `7a17edd docs(h3): pin gap repair evidence for B rereview`；
- 18 个改动文件，仅涉及任务包、run05 与阶段入口，没有改默认 PHAT、原 Tracker、录音、RTL、Vivado/Vitis 或 Skill 活动源码。

普通 Git smart transport 在本机网络失败，故从 GitHub API 下载准确 SHA tarball，在全新目录建立审核树。Windows tar 对范围外一个中文 PDF 路径报错；任务包与阶段入口共 70 个文件均逐一用 `git hash-object --no-filters` 对照远端 tree blob，差异 0。为运行包内 Git 输入/祖先检查，仅附加审查元数据；候选文件字节和身份以远端 tree 对照为准。

审核树：

`F:\NUEC\review-worktrees\h3-7a17edd-api\TophBeifong1744-Competition_fpga-7a17edd2b5408e10608d954f3e7fa11cb62fe34b`

## 2. README 单命令

环境：Windows 11；Python 3.12.14；NumPy 2.3.5。

```powershell
& 'C:\Users\BryanZheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B `
  'task-packages\PKG-B-ALG\tasks\h3-complete-20260918\source\reproduce.py' `
  --repo . `
  --out 'F:\NUEC\review-evidence\h3-7a17edd-independent-run01'
```

总退出码：`0`。输出目录此前不存在，未覆盖作者证据。

- 包清单：68 文件 PASS。
- 输入前验/后验：各 18 项 Git blob PASS，`CRLF_NORMALIZED 0`。
- H3 测试：39/39 PASS。
- 新生成 golden：14 数组和冻结事件 PASS。
- 提交中的 run05 frozen golden：单独再次检查 PASS。
- 既有三路音频入口：50 项及 render/audit PASS。
- 脚本结果字符串仍为固定的 `PASS_AUTHOR_REPRODUCTION_NOT_INDEPENDENT_REVIEW`；本次实际执行者为 B。

未受本轮改动影响的输入封存、Q12 边界、旧三路音频和 Skill 范围按增量规则复用，但仍由单命令做了包级回归。

## 3. 4513/4521 断流闭环

独立生成结果：

1. 同一个 `FixedTracker` 在 3072 后收到 4513 控制输入，间隔 1441：
   - `state=ACQUIRE`
   - `fresh_valid=false`
   - `reason=gap_reset_acquire`
   - `last_fresh_sample=null`
   - `valid_through_sample=null`
   - `discontinuity=true`
2. 该 4513 行实际存在于 `audio_timeline.control_rows`，不再是独立、未消费的 trace。
3. 共同可用延迟 8 样点，4521 触发：
   - event=`DISCONTINUITY_TO_SINGLE`
   - target bank `1 → 0`
   - previous TTL `12680`
   - new TTL `null`
4. 断流前 4513～4520 target 一直为 1，没有提前回填。
5. 关键码：

| 发声样点 | target | Q12 权重 `[single, 0°, 19°]` | automatic | single |
| ---: | ---: | --- | ---: | ---: |
| 4520 | 1 | `[0,4096,0]` | -366269 | -261312 |
| 4521 | 0 | `[0,4096,0]` | -815620 | -783040 |
| 4522 | 0 | `[9,4087,0]` | -620818 | -944992 |
| 5001 | 0 | `[4096,0,0]` | 45536 | 45536 |

这证明 4521 先切目标并清 TTL，随后开始 480 样点淡变；到 5001 automatic 已与 single 相同。

## 4. 冻结比较与文件字节差异

独立输出的 14 数组逐元素差异均为 0；Tracker 控制行和 audio timeline 规范 JSON 哈希一致。独立生成文件与提交中的 run05：

| 文件 | 字节 | SHA-256 | 字节差异 |
| --- | ---: | --- | ---: |
| `golden-stages.npz` | 110281 | `66a1c9b5edd797c9c1474ce275c13065b89ac03eccd338dcb12713cf9292c19f` | 0 |
| `golden-summary.json` | 58995 | `f848e2311bbc2333a892ac0d10bde4012403d0384a93765cb90ce6e87868aea9` | 0 |
| `golden/SHA256.json` | 191 | `5d9d6be7e85605ffd8c9a66e9f535e31640bcfe8741d02c4f36a1f3003df51d3` | 0 |
| `frozen-run05-check.json` / `run05/golden-check.json` | 6781 | `6c98c6e8502e42dd43b32df5ae6b4946f1e3a197a943b4b8eabee2fbae436fb3` | 0 |

## 5. 独立故障注入

针对提交中的 run05 冻结证据逐项修改一个值，均由 CLI 检查器拒绝：

| 篡改 | 退出码 | 失败字段 |
| --- | ---: | --- |
| 4513 control row | 1 | `tracker` |
| 4521 gap event | 1 | `audio_timeline` |
| target bank | 1 | `auto_target_bank` |
| 4522 Q12 weight | 1 | `auto_weights_q12` |
| 4522 automatic PCM | 1 | `automatic` |

状态：`PASS_ALL_EXPECTED_GAP_FAULTS_DETECTED`。因此检查器确实比较提交中的冻结控制/事件和三个关键输出数组，并非只让新生成结果自比。

## 6. 首错与历史证据

- 包内 `first-failure.redacted.log` 存在，833 字节，SHA-256 为 `216376d0db98a4c31c338c23a64e98c1005b1993c6d0f315398bce6dbaf7c00c`。
- 日志保留测试名、栈、`StopIteration`、`Ran 1 test`、`FAILED (errors=1)`，且未包含个人绝对路径。
- run05 README 声明仓库外原始日志为 950 字节、SHA-256 `DCF5A3FBE69CA7CD1D5537371B7F7A21777D770DFCCB110F71A67DD10C3762EE`；该原件未随候选提供，B 本轮不能独立核对其字节，只能确认包内脱敏件及声明。脱敏件没有伪称为原件。
- run01：10/10 文件，0 新增、0 删除、0 字节变化。
- run02：11/11 文件，0 新增、0 删除、0 字节变化。
- run03：14/14 文件，0 新增、0 删除、0 字节变化。
- run04：6/6 文件，0 新增、0 删除、0 字节变化。

原始首错日志的受控可取回凭据/完整命令仍建议补充，但因本轮 current-SHA 行为、冻结证据和五类失败注入均由 B 独立重现，它不构成 run05 软件断流闭环的技术阻断。

## Standards

规范轴报告 1 项证据管理缺口、1 项判断项：

1. **证据管理缺口**：run05 只提交脱敏日志；仓库外原始日志只有声明的哈希/字节数，没有可由 B 访问的受控制品身份及完整首错命令。它削弱开发首错的独立可追溯性。建议补充受控备份回执、失败时准确工作状态和完整命令。因隐私脱敏已如实说明，且 B 已独立验证最终行为与失败注入，本报告将其列为非技术性后续项，不扩大为 H3 通过。
2. **判断项**：控制行/事件仍以裸 dict 和字符串 kind 在生成器、消费者、测试间传递，属于可能的 Primitive Obsession/Data Clumps；可在冻结 JSON 边界外使用 dataclass/Enum。不是本轮阻断。

符合项：包内未发现个人绝对路径；run01～run04 字节未变；相对命令可移植；增量范围没有越界。

## Spec

规格轴无阻断或范围扩张：同一 Tracker 的 4513 行已进入 automatic；4521 切单麦目标、清 TTL 并按约定淡变；run05 控制/事件、bank、权重和 PCM 都被提交冻结并由独立负例验证；旧证据和限制未退步。

注意：1441 样点 gap、19°/70°仍是合成注入控制向量，不是实录、RTL 或实板断流证据。

双轴汇总：Standards 为 1 项证据管理缺口、1 项判断项，最重是仓库外原始首错不可由 B 现场核验；Spec 为 0 项发现，断流闭环增量要求全部满足。

## 7. 限制与准入范围

本轮只批准：

> `7a17edd2b5408e10608d954f3e7fa11cb62fe34b` 中 run05 软件整数 golden 的“断流控制进入 automatic，并在共同可用时刻清旧 TTL、切回单麦并淡变”增量证据，以及对应测试和检查器。

不批准、不改变：

- center/quiet 存在门仍均为 61/61；quiet fresh=0 不等于背景被存在门拒绝。
- 六秒录音 `8f708e4`仍未由本包批准。
- 73900 周期仍是历史 OOC 槽相加，不是混合位宽整链实测；91080 B 不是 BRAM 映射。
- SKL-001 仍仅模块仿真限定；SKL-002 仍仅 offline static/mock；真实 PYNQ 未运行。
- 正式方向指标、客观音频收益、AMD 全链 bit-exact、集成 RTL/时序、实时和实板输出仍为 `NOT_RUN/BLOCKED`。
- 不批准默认算法替换、完整 H3、M1 或 V1。

## 8. 明确结论

`LIMITED PASS`：上一轮唯一技术阻断“断流未进入 automatic 音频链”已关闭。本轮没有新的技术阻断，允许将准确 SHA 的 run05 软件断流闭环候选作为限定材料进入后续授权流程。

本报告未执行合入；不得据此签完整 H3 PASS。是否合入及何时办理，仍由用户/工作执行按授权决定。

## 9. 证据位置

- 单命令输出：`F:\NUEC\review-evidence\h3-7a17edd-independent-run01`
- 独立故障注入：`F:\NUEC\review-evidence\h3-7a17edd-gap-fault-injection01`
- 准确 SHA API 归档：`F:\NUEC\review-evidence\h3-7a17edd.tar.gz`
