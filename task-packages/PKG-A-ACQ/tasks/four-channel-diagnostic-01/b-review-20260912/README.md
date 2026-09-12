# B 独立复核：四路工程整理交付

日期：2026-09-12；复核人：B。结论：**通过限定工程材料与诊断辅助软件复核，可按本范围合入。** 本轮没有发现阻断此用途的内容问题。不是正式 M1、完整 H2/H3、C 板实物、声学同步/定位效果或整机时序验收。

## 固定版本与范围

- 作者远端：`codex/toph/four-channel-engineering-review-20260912`。
- 固定审核 SHA：`2aed019574683438cd1ddfad0388fecaa7d6af63`。
- 审核基点：`02a41b4507b4544e2fdf1d20a28996997110c337`。
- `git diff 02a41b4...2aed019` 为 195 个新增文件，全部位于 `task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/`；其中 189 个原件及 6 个整理/清单/验证文件。
- 独立工作树：`F:/NUEC/review-worktrees/b-a-four-engineering-review-20260912`。作者原件逐一与固定提交 Git blob 比较，195 项字节一致；测试前后哈希未变。未切换或覆盖 develop、one、其他工作树或原始录音。
- 规范：当前 AGENTS、CONTRIBUTING、team-workflow、phase-closeout；需求：DELIVERY-20260912、A 阶段任务页及 microphone-adapter-decision。

本轮只新增本审核目录，未边改作者方案边自审。已通过的杜邦线实录诊断没有重做，其独立接收依据仍在 `PKG-A-ACQ/deliveries/dupont-diagnostic-20260911/B-REVIEW.md`。

## 实际执行

Python 3.12.14，Windows；具体环境、参数、退出码、195 项保护哈希见 `evidence/run01/result.json`。全部退出码 0：

| 检查 | 结果 |
|---|---|
| 固定作者 Git blob / 执行前后文件保护 | 195 文件逐字节匹配且未改变 |
| `verify_delivery_20260912.py` | 189 项原件大小、SHA-256 匹配 |
| `unittest discover -s source -p test_*.py -v` | 17/17 通过（9 项采集门禁、8 项导出） |
| `check_sim_export.py` 使用归档 c-adapter-sim01 accepted_words.csv | 3 次、57 组、456 个 32 位字导出逐值通过 |

测试包含包数/配置/日志失败、DMA 错误、BIN 身份、来源声明、signed24、uint64 进位及溢出、顺序、间断与饱和标志。最后一项使用历史 RTL 握手输出，本轮没有重新运行 RTL 仿真，不能写成新 XSim 通过。没有运行修改 one 的 Tcl、构建、下载、复位、上电或新录音。

在仓库根目录复跑以下命令，输出必须不存在；脚本固定作者提交并核对作者全部文件，因而需要本仓库保留该 Git 历史。若作者原件以后有批准修改，应在本固定提交对应的工作树复核，不能改断言抹去版本差异。

```powershell
python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/b-review-20260912/reproduce.py --repo . --out F:/NUEC/review-evidence/a-four-engineering-new
```

运行结果中的环境、绝对路径、unittest 耗时可不同；这些不属于算法数值一致性。源文件/输入的字节哈希、导出数值和运行日志字节分别记录，不宣称跨环境所有生成文件字节相同。

## Standards

**阻断性规范违反 0；无需要单列的 code smell。** 作者说明区分整理者身份、纯软件自检、原工程证据及外部依赖。冻结源码和历史加载快照的必要重复有明确用途，不为去重修改原件。失败日志和换行保护保留。

非阻断但必须保留的入口限制：`adapt_c_one.tcl:8–10` 固定 A 的 one.xpr，Tcl 自身不拒绝已有输出目录；`build_ps.ps1:7,10` 固定 A 的临时目录和工具路径。因此只能作为对应环境的历史构建材料接收，不能登记为本机可移植、安全无覆盖的活动构建入口。以后确需活动重建，由 A 另行参数化并增加输出目录保护；本轮不改冻结文件。

## Spec

**阻断性需求问题 0；未发现本次发布整理的范围扩张。**

- `four_mic_top.v` 保持一个分频状态驱动四个 CLOCK 端口，DATA1～4 对应 mic0～3。mapping JSON、XDC 与决定页记录一致；这属于配置核对，不是独立测量物理引脚或时钟偏差。
- RTL、PS 和 exporter 一致采用 32 字节八字记录：64 位原始 ID、四路符号扩展 signed24、饱和 flags、保留字。32000 组 ×32 =1024000 字节，加 64 字节 guard 小于 1 MiB，128 包×8000 字节一致；未擅自扩大到 48000 组。
- RTL 对 valid 失配/满 FIFO 记录 fatal，PS 在采集/最终状态检查并拒绝失败段；正常再次采集与复位恢复分开。TB 静态检查覆盖背压稳定、尾包、busy 重复 start、再次采集和复位，但本轮未新运行 TB，也未穷举全部参数。
- 采集门禁核对完整串口/BIN 的配置、包数、状态、FNV、编号；通用导出器保留调用者来源声明，synthetic 不改标真实录音。无几何坐标时不生成 DOA 精度结论。

## 批准文件和使用位置

批准准确作者版本的全部 195 项文件作为工程工作源码/历史证据与诊断辅助软件入库，加本 B 复核记录和可复跑软件证据。继续使用已有任务包中的 `source/export_four.py`、`source/export_c_capture.py` 作为相应诊断导出入口，B 接收仍复用主线既有 `PKG-B-ALG/tasks/four-channel-receipt-01/diagnose.py`。不复制一份平行活动算法。

本次不替换 `rtl/`、`ps/`、BD/XDC 或实际 one 工程。原因：本包是原成果整理与软件复核；新位置整机重建、环境独立性和物理条件并未验证。若后续正式接入，需要针对现有唯一工程核对源码来源/配置、处理外部依赖并完成对应集成验证，不直接运行旧固定路径脚本。该限制不阻断本次材料归档，也不要求重做已通过的实录交接。

外部 one/BSP/epro2/历史 recovery 不在公开包，本次未取得或运行，不宣称完整现场复现；需要时由 A 按 DELIVERY 的恢复方法在新目录提供对应项。完整外部 IO delay、物理同步、实测采样率、C 转接板实物、PS 中止后的现场恢复及长期稳定仍未验收。

本轮规范与需求轴各 0 项阻断；批准仅在上述范围。发布 SHA、合并后验证和本地/远端收尾见同目录 PUBLICATION.md 及其 Git 历史。
