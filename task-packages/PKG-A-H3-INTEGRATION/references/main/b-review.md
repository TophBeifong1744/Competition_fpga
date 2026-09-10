# A 复核：input-boundary-adoption-01

日期：2026-09-10。结论：**通过，仅批准自包含输入边界采用与候选预算草案入库；不冻结候选数制。**

## 版本与批准范围

- 实际审核提交：`80a7b929fa6ec072b1ad41d566c8f2067a5231e2`。
- 实际远端分支：`review/member-b-budget-to-a-01`；PR #5。
- main 基线：`797cdd09425c09c56ed4e0034fc1912b45b4b878`。
- 已批准 A 边界：`d262f275ed6817b07f732d5c85f675fd4ebeccdc`，与 main 中活动边界文档一致。
- 仅批准 `task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/` 的原始 9 个文件，以及本轮 A 复核记录、脚本、复跑证据。

该提交另带 fixed-das-01（12 文件）、fixed-point-contract-01（8）、implementation-budget-01（14）、three-way-audio-01（37）、tracked-audio-01（55），合计额外 126 文件。它们不在本次批准范围。A 采用限定目录导入，不整支合并 PR #5，不据此批准其他算法/音频任务。包内历史快照仅作为本预算依赖保留，不等于批准它们对应任务。

## 复现与独立检查

在独立 detached 工作区 `E:/Users/Toph Beifong/Documents/GitHub/ss-b-budget-review` 固定上述 SHA，保留提交原始文件；另在 main 基线的隔离集成工作区仅导入批准目录。

Python：3.12.14。实际解释器：`C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。

首次在包目录执行（与仓库根目录入口等效）：

```text
python -B prepare.py --out evidence/a-review-run01
```

限定目录导入后的回归，在仓库根目录执行：

```text
python -B task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/prepare.py --out evidence/a-integration-run01
python -B task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/evidence/a_budget_check.py task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01
```

注意 prepare.py 将相对输出路径解析到本包，而非当前工作目录。输出目录须不存在。

检查结果：作者入口 PASS；A 独立预算算术检查 PASS；3 个快照与清单哈希一致，在完整审核副本中也与来源路径文件一致。首次 evaluation.json 与作者 evidence/run01/evaluation.json **字节一致且语义一致**。未改动作者配置、快照或历史证据。该检查不是完整定点算法测试。

| 独立复算项 | 结果 |
|---|---|
| 帧率 / 带内频点 | 93.75 帧/s；79 点，索引 7..85 |
| FFT/IFFT 软件变换数 | 每帧 6 / 最多 15；不是 IP 延迟 |
| 窗乘 / 互谱、模长、复数除实数 | 6144 / 各 7695，每帧 |
| 合法时延搜索点 | 12 条 40 mm 基线、3 条 sqrt(2)*40 mm 基线，共 207 点 |
| 全复变换等效输入吞吐 | 2,016,000 点/s，不是处理周期 |
| 当前音频预算 | 两支滤波器分开累加，54+12=66 MAC/输出；3,168,000 MAC/s，混合及管理另计 |
| 增长候选部分存储 | packed 84,551 B；逐元素对齐 92,572 B；软件容器 132,837 B |
| 缩放候选部分存储 | packed 75,317 B；逐元素对齐 84,364 B；软件容器 100,005 B |

音频 54/12 项是本包沿用的实现结构上界，不是对其来源 tracked-audio 任务的独立功能验收。未复现范围外音频任务的全部结果。

## 边界与数制判断

三类输入正确分离：signed16 测试码型桥接候选保持整数、不左移；H1 四路 signed24/int32 右对齐符号扩展，浮点除以 2^23；六麦合成浮点保留幅度，公共增益与超范围策略待定。文件 fractional_bits=0 与算法 S24F23 不混用。

PL 目标含实时采集、FFT/PHAT/IFFT、TDOA/LS/秩与质量、跟踪、连续 DAS；PS 为配置、缓冲、导出与 UI。与 A 已批准部署边界一致，未把离线 Python 当 PS 实时实现。

两候选互谱位宽满足复乘扩位要求；54 位音频累加器满足分别累加最多 54 项的保守计数界；窗及音频权重可精确表达 1。当前候选可继续研究，但下列限制必须延续至下一轮：

1. S24F23 正端点是 `1-2^-23`，不是 +1。README 的 `|x|<=1` 是解析幅值前提，不能宣称所有端点无损编码；+1 舍入后的饱和计数须进测试。
2. 总右移 10 不证明逐级无溢出。窗口乘积舍入点、FFT 每级缩放、IFFT 归一化和指数补偿尚未冻结。不得从本次范围算术推断零饱和。
3. PHAT epsilon 与 FFT 缩放后的物理量必须保持对应。S69F46/S51F46 的量化步长为 2^-46，不能直接把物理 epsilon=1e-15 四舍五入为零后沿用；需显式阈值/指数及低能量保护方案和测试。
4. evaluator 的宽范围上界使用 float 展示，例如 S69F46 最大值可能被打印为 4194304.0；真实最大值是 `4194304-2^-46`。这是展示精度限制，后续整数 golden 必须以整数码界为准。
5. prepare.py 的 PASS 只检查有限断言、哈希和预算，不覆盖所有合同字段的负例，也不证明 FFT/PHAT 误差、跟踪离散状态或音频性能。
6. 部分存储可用于候选对比，不能当全系统下界或资源承诺。FFT 内部/全谱装配与重排、twiddle、模长/倒数、LS、FIFO、CDC、DMA 对齐、状态及双缓冲生命周期需在真实调度中补齐；单麦对工作区复用必须有时序依据。

## A 返回的工程状态

| 项目 | A 本轮确认 / 未确定项 |
|---|---|
| 工具与器件 | 沿用已确认 Vivado 2025.2、xc7z020clg400-2；不据此猜测 FFT IP 版本 |
| 当前 BD 时钟 | 本轮只读 one/system.bd，FCLK0 配置仍为 100 MHz；仅作预算场景，不是声学处理时序通过 |
| FFT IP/版本/架构 | 当前核对 BD 未实例化 xfft；继续待定，不能把 Vivado 版本填成 FFT IP 版本 |
| FFT 点数/变换需求 | 六麦候选 N=1024、6 FFT+15 IFFT/帧；硬件映射、次序和重排待确认 |
| 缩放 | 增长 0、缩放 10 仅为两种候选总右移；逐级 schedule、指数、IFFT 1/N 与 PHAT 阈值映射待定 |
| 周期/吞吐 | 处理时钟、变换延迟、启动间隔、背压及其他处理周期继续 null；100 MHz 场景每 hop 1,066,666.666... 周期，固定整数上限保守取 1,066,666，不能把四舍五入当保证 |
| RAM/DSP | 内部占用、系统分配额度、端口并发和安全余量待定；本包部分字节清单不代替综合估计 |

下一步 A 提交独立最小 FFT 配置及配置导出、变换测试、周期/启动间隔测量与资源估计；B 可先做参数化逐级量化研究，但不得称与最终 IP 位精确一致。最终板测无需阻塞草案研究，工程配置未明确则不得冻结部署数制。

## 验收限制

仅批准草案归档与参数化研究的依据。不批准默认算法替换、完整定点算法、资源/时序/实板、四麦主线或 H2/H3。没有修改 RTL、共享 one 工程或其他成员内容。未来生成 RTL 时继续遵守项目当前 RTL/BD 集成规范，本轮不实施 RTL。
