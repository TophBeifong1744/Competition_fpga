# B 独立复核：SKL-001 / SKL-002，2026-09-14

两项分别判为 **NEEDS_FIX**；本轮批准 SHA、批准实现范围、main 合入提交均为**无**。基础复跑通过不能覆盖已复现的合同漏检。A 修复后须提供新的准确远端 SHA，重新复核；本记录不预先批准修订版。

本记录与[原始证据入口](../../results/skill-review/b-20260914/README.md)已按用户后续明确授权推送到 `review/member-b-skills-20260914`，首个准确发布提交为 `f37f4be0052ceb38ec909803943e36554c62b18e`。此前上传曾被自动权限审核拒绝；用户明确允许上传复核报告、源码快照和日志后，才继续执行，没有绕过拒绝。随后仅补记实际发布结果，最终反馈分支 SHA 见用户回报，避免自引用。未把反馈分支合入 main，两个候选分支均保留。远端 main 仍为 `57c50e6c99731cd57e7738ac91b02f985ad229b1`，本轮未改其内容。

## 版本、环境与复核方法

| 项目 | 固定身份 / 申请范围 |
| --- | --- |
| SKL-001 0.3.0 | `c562466805aff08201cd457cc2e6ee7464a3566f`；`skill/fpga-module-verification/`、`task-packages/PKG-A-SKILLS/` |
| SKL-002 | `55039cf8bfab2bd6112192c8bd646d427a52a642`；`skill/pynq-overlay-dma-validation/` |
| 共同父提交 | `ccaeae1c0ac9be07e006ffed09cb7f16bf064906` |
| 远端核对 | 开始及用户暂停/恢复后，以本机 `gh api .../git/ref/heads/...` 直接核对 main 和两个候选，均未变化 |
| 干净输入 | 两个独立 detached 工作树 `F:/NUEC/review-worktrees/b-skl001-c562466`、`b-skl002-55039cf`；不用共享混合目录 |
| 实际工具 | Windows；`D:/Python/python.exe` 3.13.0；`D:/AMD/2025.2/Vivado/bin`，Vivado/XSim 2025.2，SW Build 6299465 |
| 结构工具 | 本机系统 skill-creator `quick_validate.py`；已有 Anaconda Python 3.7.0 / PyYAML 3.13，启用 UTF-8；两项均通过，无软件安装 |

先读最新 main 的 AGENTS、team-workflow、skills-delivery-plan 和 9/14 publication，再读准确候选各三份指定材料。原包“未提交/未发布”是历史记录，以后续发布 SHA 为准，没有重写证据或清单。Git HTTPS 不通、连接器仓库不可见，但已有 gh API 可用；缺失对象通过 API 读取并按 Git blob/tree/commit 重算 SHA 后写入本地对象库，没有用下载快照伪装准确提交。此网络绕行已完成，不把它列为候选环境阻塞。

基础复跑由 B 执行。另一次陌生模块前向使用由无历史上下文的隔离执行方完成；只给 Skill、需求、必要 RTL 和工具路径。B 再独立读 TB、检查实际日志，并用另行计算的 golden 对全操作数输出核对；不把作者测试或代理回报当作 B 批准。没有测量有/无 Skill 的效率差异，不给出 AI 效率提升百分比。

## SKL-001：NEEDS_FIX

### 实际通过的测试

从准确候选仓库根目录执行（本机 `python` 实际选择上述 Python 3.13，完整 argv 见每个 `command.json`）：

```text
python -B -m unittest discover -s skill/fpga-module-verification/tests -v
python -B skill/fpga-module-verification/scripts/run_examples.py --vivado-bin D:/AMD/2025.2/Vivado/bin --output F:/NUEC/review-evidence/skills-b-20260914/xsim-examples
```

| 测试 | 实际结果 | 原始证据目录 |
| --- | --- | --- |
| runner 单元测试 | 7 项通过，退出 0 | `skl001-unit/` |
| PCM，宽度 2/24/32 | 792 次比较，PASS_SIMULATION | `xsim-examples/pcm4/` |
| elastic，宽度 1/8/16 | 1125 项检查，PASS_SIMULATION | `xsim-examples/elastic/` |
| 数据位故障 | 编译/展开成功；仿真首错 width=1, cycle=9, transaction=0, expected=0, actual=1 | `xsim-examples/bad_data/` |
| ready 故障 | 编译/展开成功；仿真报 empty acceptance | `xsim-examples/bad_ready/` |
| 恢复原源、相同输入 | 1125 项检查再次通过 | `xsim-examples/restored/` |
| 陌生 signed8 饱和加法、单级 ready/valid | 原输入 `-128 + -1` 错出 `-127`；仅改测试用 RTL 的下饱和值；相同 TB/case/合同复测 66,343 笔输入、337,372 次检查 | `forward/runs/01_original/`、`02_fixed/` |
| 陌生模块 X/Z 变体 | 同一 TB 均在仿真阶段检出 unknown payload | `forward/runs/03_mutant_x/`、`03_mutant_z/` |
| B 独立数值 golden | 全 65,536 组输入，独立 Python 整数模型与实际输出逐字节一致，0 差异 | `b-golden/`、`xsim-b-golden/` |

陌生模块 TB 经 B 审阅：负边沿驱动，正边沿取握手和旧输出，NBA 后核查新寄存值；显式拒绝 X/Z；复位丢弃两笔在途事务；66,343 accepted = 66,341 consumed + 2 discarded；最终排空。全速、空槽接收、同时消费/替换、固定种子停顿、复位优先和逐拍延迟均有观察。独立 golden 在盲执行完成后、B 自己的输出采集前生成，未提供给执行方，不冒充提前封存的参考答案。

### 必修 S1：示例 TB 未约束合同中的一级延迟和容量（P2）

位置：[准确候选 tb_elastic.sv 第 35 行起](https://github.com/TophBeifong1744/Competition_fpga/blob/c562466805aff08201cd457cc2e6ee7464a3566f/skill/fpga-module-verification/examples/elastic/tb_elastic.sv#L35)、第 49 行和第 80 行；合同第 3 行明确 `One registered slot`、`latency one edge`。

复现：仅在隔离 `latency-mutant/elastic_stage.v` 中把两个正确一级 stage 串联；原 TB、case 和合同字节不变。用候选 `run_xsim.py --case <证据>/latency-mutant/case.json --vivado-bin <2025.2/bin> --output <全新目录>`。实际编译/展开/仿真成功，原 TB 打出 **PASS_SIMULATION / 1149 checks**。其队列只在输出握手时比较，最后允许四拍排空，没有逐拍证明输出到达时间或最多一笔在途。

预期：两级副本违反一级合同，应 FAIL_SIMULATION。B 的最小同输入对照已实际证实：在首个接收边沿后的观察点，正确原 RTL `out_valid=1, data=5a`，两级副本 `out_valid=0, data=00`；独立 TB 判原件通过、两级副本失败。见 `xsim-b-latency-original/` 和 `xsim-b-latency-two-stage/`。这不是工具启动失败，也不是正确原 RTL 被判错。

A 应在示例 TB 中补上符合其合同的逐拍有效/数据到达和一级容量检查，并保留该负例回归；不能只缩短 drain、改合同为两级或调整 PASS 计数来避开。B 没有修改作者 Skill/TB/RTL。请求完成本项后重新固定候选 SHA。

### 文档与范围

README 已说明用途、命令、失败边界、作者实测效果、C 的 PCM 来源与仓库 MIT 许可，引用了小写竞赛导出/安装时恢复 SKILL.md 的方案。可见纠错摘要及刻意故障身份明确。最终比赛压缩包的路径/安装导出实际演练本轮 **NOT_RUN**，不把现有方案说明当最终提交验收。

## SKL-002：NEEDS_FIX

### 实际通过的测试

从该准确候选的 Skill 目录执行，三个输出名均全新：

```text
python -B scripts/run_offline_tests.py --output results/b-review-tests.json
python -B scripts/simulate_dma.py --contract references/example-session.json --output results/b-receive.json
python -B scripts/simulate_dma.py --contract references/example-session.json --fault timeout --fault abort-timeout --output results/b-timeout.json
```

实际为 **50 项测试方法、39 个 subtest 全通过**；前两条退出 0。第三条退出 1、FAIL、`buffer_disposition=retained`、`session_blocked=true`，无 rx.read/release；这是符合预期的故障证据，不能列为普通回归失败。结果原字节另存 `skl002-required/`。

B 另建 thermal signed16（96 bytes）及 pixel uint32（128 bytes）两套不同题目、器件声明、控制/DMA IP、16/64-bit 流宽的合成 profile；静态检查与外部 golden 驱动的单向接收复用同一核心。两套各跑正常、缓存陈旧、部分启动+停止失败、状态不可读、双超时、短包及释放异常，共 14 次 session，逐一检查未静止不读不释放、失败后不重试、释放最多一次。`2**120` 相差 1、容差 1、binary64 极值容差溢出、短数组/短字节也正确处理，见 `skl002-independent/`。

这些是参数化 static/mock 复用，数据格式由 B 的外部 payload/golden 定义；不是两块实板或任意算法识别。`pynq_probe.py --download` 仅验证 guard，非零返回 `BOARD_RUNNER_NOT_QUALIFIED`，没有硬件报告、Overlay 下载或真实 DMA。mock 耗时和吞吐字段均按合成时钟理解。

### 必修 D1：合同 IP 可不存在于 HWH，静态验证仍 PASS（P2）

位置：[validate_profile.py 第 192–202 行](https://github.com/TophBeifong1744/Competition_fpga/blob/55039cf8bfab2bd6112192c8bd646d427a52a642/skill/pynq-overlay-dma-validation/scripts/validate_profile.py#L192)、第 212 行、第 268 行。

输入：`skl002-independent/thermal/missing-dma-ip.json` 或 `missing-control-ip.json`。仅把对应 `dma_contract.ip_name` / `register_contract.ip_name` 改成 `not_in_hwh`；同目录合成 HWH 只有 `thermal_control` 和 `temperature_dma`，manifest 哈希仍真实匹配。

```text
python -B scripts/validate_profile.py --profile <证据>/skl002-independent/thermal/missing-dma-ip.json --mode offline --output <全新报告.json>
```

预期：合同指向不存在的 IP，应非零/FAIL。实际：两个输入都退出 **0 / PASS**，见 `cli-missing-dma.json`、`cli-missing-control.json` 及 `skl002-cli-*/command.json`。代码只检 `overlay.required_ip`，没有把实际合同所用 IP 与清单/HWH 绑定。A 应使 register/DMA 合同的实例必须在同构建 HWH 中可解析，补两条负例；不能为真实 S2MM-only 工程编造 MM2S 或身份寄存器。

### 必修 D2：重复测试 ID 用后条成功掩盖前条失败（P2）

位置：[validate_profile.py 第 436 行](https://github.com/TophBeifong1744/Competition_fpga/blob/55039cf8bfab2bd6112192c8bd646d427a52a642/skill/pynq-overlay-dma-validation/scripts/validate_profile.py#L436)。

输入：`thermal/profile.json` 与 `thermal/duplicate-evidence.json`。`dma_runs` 两条均为 `fixture-loopback`；前条 `timed_out=true,mismatch_count=4`，后条成功。其他身份、长度、cache 等匹配。

```text
python -B scripts/validate_profile.py --profile <证据>/skl002-independent/thermal/profile.json --evidence <证据>/skl002-independent/thermal/duplicate-evidence.json --mode offline --output <全新报告.json>
```

预期：拒绝重复 ID 或明确报告该组含失败，不能无声丢弃。实际：退出 **0 / PASS**，报告只显示后条成功，见 `cli-duplicate.json`。字典推导式覆盖早前记录。A 应拒绝/显式区分重复记录，并测试不同排列不会掩盖失败；这不否认独立 DmaSession 运行器已有的失败阻断行为。

### 必补 D3：独立 README 的来源、许可和分发说明（P2，交付完整性）

位置：准确候选 `README.md`，尤其第 61 行起的“可复用性与比赛报告”至文末。已有场景、命令、边界、效果和工程输入来源；未明确自有脚本的许可/第三方来源边界，也没有独立 Skill 的提交路径映射或对项目导出规则的直接入口。根仓库有 MIT，但应在交付 README 中说明适用范围并保留许可文本/来源，不让独立使用方推测。历史作者“未提交”不在此缺陷内，不要求改写原始哈希证据。

## 原件、哈希和格式

[evidence-audit.json](../../results/skill-review/b-20260914/evidence-audit.json)记录：SKL-001 141 个申请范围文件、SKL-002 21 个范围文件均与准确 Git blob 逐字节相同；相对共同父提交的变化没有越界。SKL-001 manifest 140 项及归一化 PCM 外部输入通过；PYNQ 两份作者报告和 B 新报告共 30 条绑定（10 个不同源码/输入）通过；23 份历史/本次 XSim result 的输入快照、合同、case、日志哈希均一致。

SKL-001 `xsim-01` 是历史源，`xsim-02` 对应当前源，不把前者当当前测试。没有为格式检查改作者证据。两项去掉 immutable evidence 的实现/文档 `git diff --check` 通过；包含原始证据时分别出现 3976/484 行换行或空白告警，原日志保留。结构验证器通过仅说明封装结构。

## 限制、处置与修复回交

两项均无批准 SHA，未合入/推送 main，故 main 合入后测试 **NOT_RUN（没有已批准变更可合入）**，不是遗漏一次已授权成功合入。复核反馈分支只含本记录和可恢复证据，不含对作者活动源码的修复。修复由 A 原任务完成，不另派 C，不改变 B 的 9/18 算法主线或 H1/H2/H3。

真实 PYNQ 镜像/驱动、物理板身份、Overlay/真实 DMA/TLAST、综合实现、资源、STA 时序、CDC、板测、长稳和整机能力全部 **NOT_RUN**。有限仿真或离线实现通过也不等于 10/1 Skill 总验收、整机通过或固定比赛加分。

候选短期分支未完成，两个都保留。本机原脏 `F:/NUEC/develop` 及其他算法工作树未切换/重置；独立复核树的有用新增输入、源码快照、报告、原始日志集中到本反馈分支，模拟器 work 缓存可按日志重建。A 的电脑及其 162 项本地差异不可访问，**未处理、未代签已清理**。具体本机 refs、材料去向、删除/保留清单及发布核对见证据中的 `closeout.json` 和用户回报。

给 A 的回交要求：分别修 S1、D1/D2/D3，保留本轮及作者旧证据；给出新任务 SHA、变化范围和新的测试输出；两项可以分别回交和复核，不必等齐。反馈已通过上述仓库分支提供；本轮没有通过聊天工具向 A 设备派发消息，不称 A 已阅读或接收。
