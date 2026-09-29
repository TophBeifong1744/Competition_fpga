# PR36 来源与映射补述（2026-09-29）

状态：**C 本人已确认现场陈述；加载来源接受范围待 A/M 裁定。** 本文是事后补述，不是采集当时的预检或授权。
固定候选 `afa513e44bec8cbb51ad42ab6bc8ac04b4de4185`；原分支 `codex/15-c-recording-evidence`；对应 #15 / PR #36。A 核对基线 `11053af5ab15b7593d418cfdc4bf615d549d5e66`。

## 结论与证据等级

- 映射连续性：按本轮用户转交的 A/M 2026-09-29 确认，19 Run 沿用 9/13 同一 C 板、同号插接和 mic0～3 映射，期间未换线/换通道。A 原话“我能确认沿用原映射，加载记录另补”。等级 **USER_REPORTED**；M 没有另行联系 A，不冒充独立逐麦激励或精密几何实测。
- 加载来源：本次找到了真实的历史 Vitis 启动/下载活动日志，补强当时工作区、配置及路径依据；日志未带录音 ID、采集时工件哈希或成员批准事件，**19 Run 的准确加载绑定和历史加载授权仍 UNKNOWN**。
- 当前文件身份、历史运行日志、操作者事后陈述和 UNKNOWN 分开列示。当前哈希、UART build 字符串和“未变”回忆都不升级为自动实载证明。
- 补述是否完整与 #15 是否通过分开。若授权记录无法恢复，交 A/M 裁定可接受范围；本文件不自行批准或关闭任务。

## C 现场陈述与尚未知项

C 先报告“跟以前一个操作和配置；后面的复位指的是什么”，随后对“原16段与新增3段沿用以前的操作和配置”明确回复：**“确认，采集的时候没复位，不用复位”**。因此按本人事后确认记录同一操作和配置，以及采集时未复位（USER_REPORTED，确认日期 2026-09-29）。
既有 9/28 README/version-binding 记录 C/hsc119 是操作人，两原批实际用 `vitis-capture-import_app_hw_1`，ELF/bit 自录音后未变；这些既有事后记录按原范围引用。本轮简短回复不另行证明操作者账户、逐 Run 动作或工件内容。
三新 Run 原 manifest 已记录同对应旧批的板上程序等条件为 USER_REPORTED。**是否重建过 ELF/bit/平台、逐项是否更换配置或平台，未获得本轮逐项陈述；UNKNOWN，不从“相同操作配置”扩写。**
C 已明确陈述“采集的时候没复位，不用复位”，本补述记录为采集时未复位（USER_REPORTED）。历史 launch 配置同时保留 `resetSystem=true`：这是启动配置请求，不是逐 Run 采集过程的板上观测，且缺少启动事件与具体录音的绑定。启动阶段是否发生自动复位及其与每段采集的先后关系仍 UNKNOWN，不改日志，也不把“采集时未复位”扩展为整个启动过程无自动复位。“不用复位”作为操作者说法原样留存，不作为所有场景均无需复位的工程判据。无需现在操作设备。
原16段日期按 B 历史评论转述的用户确认写为 2026-09-22；具体时间 UNKNOWN。三新 Run 日期/时间 UNKNOWN；2026-09-29 是交付日及本补述日，不由 mtime 或启动日志日期反推采集日期。

## 9/13 物理映射及本次连续性声明

| 逻辑通道 | 麦接口 | DATA / J4 / 球位 | CLOCK / J4 |
|---|---|---|---|
| mic0 | U3/U4 | DATA1 / 17 / Y9 | CLK1 / 21 |
| mic1 | U5/U6 | DATA2 / 19 / W10 | CLK2 / 23 |
| mic2 | U7/U8 | DATA3 / 33 / W14 | CLK3 / 29 |
| mic3 | U9/U10 | DATA4 / 35 / V15 | CLK4 / 31 |

历史照片观察方向：左上 mic0、左下 mic1、右下 mic2、右上 mic3；+X=mic0→mic1，+Y=mic0→mic3。只引用 9/13 的操作者几何声明，不把图上方向当新的测量。
四份来源 `source/c_adapter_mapping.json` 和 `batches/c-adapter-first-20260913/{GEOMETRY.md,operator-record.json,HANDOFF.md}` 的逐文件 SHA256/OID 见附带 JSON。M 通过固定 11053 GitHub API 读字节，核对与候选 afa513 同路径 blob 4/4 相同；本地没有 11053 对象，未声称本地 git show 成功。
A/X 早先评论的映射记录缺失结论保留为当时快照；本次以用户转交的 A 本人声明补述连续性。无直接矛盾原件被本轮发现；未做独立声学映射或精密几何标定。

## 新找到的历史运行记录

来源工作区：`C:\Users\hsc\Documents\Codex\2026-09-20\wo-m\outputs\vitis-capture-import`；本次原字节复制 `_ide/logs/ide.log` 与 `vitis.log`，原路径未修改、未执行。

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| [ide.log](ide.log) | 104718 | `41c4bf68fa41c05212aae1165f6d9d68104a0bb3707b1bbac9fa44588d19f02c` |
| [vitis.log](vitis.log) | 99301 | `bc69be1cc89d1cd75680c615e31c1f72f213cf3bd732b1ce3999cd507eb5f76b` |

`ide.log` 记录 48 次启动配置，均为 `vitis-capture-import_app_hw_1`，`resetSystem=true`、`programDevice=true`，bit 路径指向 `system_continuous_20260915.bit`，ELF 指向该工作区 `files/four_mic_endurance.elf`。这里只统计已保存日志，不声称覆盖全部历史操作。

| 日志中日期（时区未显式标注） | 启动配置条数 | 原日志配置行号 |
|---|---:|---|
| 2026-09-22 | 12 | 2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62, 68 |
| 2026-09-23 | 27 | 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156, 162, 166, 172, 178, 184, 190, 196, 202, 208, 214, 220, 226 |
| 2026-09-29 | 9 | 232, 238, 244, 250, 256, 262, 268, 274, 280 |

`vitis.log` 包含 ELF 下载命令和设备配置成功消息；以下只提供定位示例，不将其按顺序分配到录音：
- `vitis.log:67`：device_configured_message（原文见日志/JSON）。
- `vitis.log:76`：elf_download_command（原文见日志/JSON）。
- `vitis.log:87`：device_configured_message（原文见日志/JSON）。
- `vitis.log:96`：elf_download_command（原文见日志/JSON）。

9/23 的启动活动不直接推翻原16段的用户报告日期，也不证明哪些活动产生这些录音；缺少 Run 对应关系，两个层次并列保留。日志路径相同不证明路径中的文件当时字节相同。
旧 README/version-binding 中“尚无自动 Run 日志”的说明是当时的检索快照，本次增补找到的日志，不覆盖旧文件。采集时 load preflight 和板上读回仍未找到，也不要求补造。

## 当前主机文件身份（非当时加载读回）

| 工作区相对路径 | 字节数 | SHA256 |
|---|---:|---|
| `files/four_mic_endurance.elf` | 308168 | `4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6` |
| `_ide/system_continuous_20260915/system_continuous_20260915.bit` | 4045690 | `b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf` |
| `files/system_continuous_20260915.xsa` | 612051 | `b84e93631132a3838cc9dadc1ce9037f2685d4d10de0b1655c76291663a8f60b` |
| `_ide/system_continuous_20260915/ps7_init.tcl` | 27896 | `a158fcc7d723b21003864159006e781ffaf5e8df24ec9b1d9279f9d14ff3ee5e` |

以上四个哈希与来件及既有候选记录一致；其 A 历史工件来源按 A/M 已核对结论引用，本轮没有重做 A 机工件链审查。PR29 获批候选 `e4bd1dd3a317a9cae2bc6834c70f80dd678c4c8b`、合入 `28d58e908525d1de1c018eeb99fd607a07b6047c` 仅涵盖 A 机既有路径静态检查，不覆盖 C GUI Run，也不能把 9/24 批准倒填到 9/22。

## 19 Run 补充表

I=`measured-direction-indoor-01`；O=`measured-direction-outdoor-01`；N=`rerecords-20260929`。每行 BIN/LOG 的完整路径、字节数、SHA256、候选 blob OID 均在 [JSON 原件索引](PR36-SOURCE-ADDENDUM-audit.json) 的 `runs[].files`。本轮只做文件身份检查，没有声学重算。

L1=既有 C 9/28 操作人回忆：同一命名 Run、ELF/bit 未变；L2=新 manifest 与 C 本轮已确认的“同操作配置”事后陈述。C 本轮“采集时未复位”的 USER_REPORTED 陈述覆盖以下19段，不意味着日志已逐段绑定。H=本工作区历史日志，仅作群组背景，不存在逐行唯一匹配。A1=本次 A 转交的全19段映射连续性陈述。

| Run | 来源组 | 采集日期/等级 | 加载来源陈述 | 历史日志 | 物理映射 | 精确加载绑定 / 历史授权 |
|---|---|---|---|---|---|---|
| bg_od | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az000_r1 | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az000_r2 | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| azm045_r1 | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| azm045_r2 | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az045_r1 | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az045_r2 | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| bg_post | I | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| bg_od_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az000_r1_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az000_r2_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az045_r1_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| az045_r2_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| azm045_r1_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| azm045_r2_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| bg_post_otd | O | 2026-09-22 / USER_REPORTED | L1 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| indoor-az000-r1-new | N | UNKNOWN | L2 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| indoor-az045-r1-new | N | UNKNOWN | L2 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |
| outdoor-az045-r1-new | N | UNKNOWN | L2 | H（未逐段绑定） | A1 / USER_REPORTED | UNKNOWN / UNKNOWN |

同一 A1 可覆盖19段，依据是用户明确转交的 A 全集合确认。L1 覆盖原两批16段，L2覆盖新3段；覆盖集合不是由日志次数或数组顺序推断。H 不声明其48次启动就是这19次采集。

## 查找范围、未找到记录与剩余影响

本轮只读固定候选的两批 capture-index/version-binding、配置证据包、重录 manifest/README；读取上述明确指向的 Vitis 工作区 `_ide/logs`，X 对该工作区文件名作有界日志/收件/授权候选检索；未扫描无关私人聊天、账号或其他用户目录。M只读原 #15、PR36、两指定复核评论及日期评论；没有把整个历史消息库作为已检索范围。
在这些范围内没有找到可唯一绑定19 Run的采集时预检/工件哈希、板上读回、A 对当次加载的授权消息或带 Run ID 的发包收件记录。此处“未找到”不表示历史从未发生；未经检索或C尚未提供的其他消息/收件渠道为 UNKNOWN。
本轮新增日志仅补强运行活动和路径来源。历史加载授权仍不可恢复时，由 A/M 判断本批开发诊断范围是否接受；不能由 C/AI 自行改为通过或降为归档并关闭 #15。

## 原批准、验证与写入归属

- [B 本人限定接受](https://github.com/TophBeifong1744/Competition_fpga/pull/36#issuecomment-5889066762)：既有全量交付身份、导出及三段有条件开发诊断输入按未变范围**复用，未重跑**。不扩展为完整 S1 CLI/H1、正文、实际加载或 #15 整体通过。
- [A/X 来源核对及缺件](https://github.com/TophBeifong1744/Competition_fpga/pull/36#issuecomment-5890133925)：本次沿该表补述，不修改其原快照。
- [原16段日期的历史转述](https://github.com/TophBeifong1744/Competition_fpga/issues/15#issuecomment-5808875877)。
- [#15 原合同](https://github.com/TophBeifong1744/Competition_fpga/issues/15)仍要求 A 接收工程来源。无 merge、关闭或审批状态变更授权被本次材料自动触发。
- 新增执行仅为哈希、固定 Git/API 身份和日志文本检查。19组38个 BIN/LOG 与候选 blob 及声明 SHA256 全部一致；原配置目录6个既有文件在写入前后哈希保持相同。未重算284文件声学结果，未构建/下载/复位/新采录。
- X 提供只读发现和机械核查；任务中断后M接管单一写入方，编写此文/JSON及复制两个日志。未改产品、原 BIN/LOG、CSV/WAV、旧 metadata、截图、失败段或 B 验收资产。本文与 JSON 是新增资料，不称独立成员批准。

## 本人确认与交付边界

C 于本任务明确回复“确认，采集的时候没复位，不用复位”，确认前述原16段与新增3段沿用以前操作和配置。现场陈述确认 **CONFIRMED / USER_REPORTED**；它不是 A 的历史加载授权或独立技术验收。
新3段采集日期/时间、是否重建各工件及启动阶段自动复位与具体录音的关联仍保留 UNKNOWN。只提交本补述、JSON及两份原字节历史日志；旧材料与批准范围不变。A/M 负责接收剩余来源范围，不 merge、不关闭 #15、不改变审批状态。

详细原件身份和补述证据索引：[PR36-SOURCE-ADDENDUM-audit.json](PR36-SOURCE-ADDENDUM-audit.json)。
