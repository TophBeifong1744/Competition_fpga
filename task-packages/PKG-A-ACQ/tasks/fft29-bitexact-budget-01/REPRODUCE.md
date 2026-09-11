# 复跑入口

环境：Windows、Vivado/XSim **2025.2**（本轮 build 6299465）、器件 `xc7z020clg400-2`、FFT IP 9.1 rev15、Python 3.12 + NumPy（本轮 2.3.5）。不需要运行 B 的声学生成器或下载 AMD C 模型，供应商 IP 由本机 Vivado 生成，不随包复制库。

所有新输出必须用不存在的目录。**不要在作者的 `evidence/run01` 或 B 原件目录复跑。** 独立短路径能避免 Vivado 的 Windows 长路径问题。本包保留 60 个原始 NPZ，因此复跑不依赖 B 当前工作树或网络。

## 快速核对归档结果（不启动 Vivado）

在本交付提交的仓库根目录运行；Python 路径换成本机可用解释器：

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$task = (Resolve-Path 'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01').Path
& $py "$task/source/package_manifest.py" check
& $py "$task/source/test_checker.py"
& $py "$task/source/check_resources.py"
& $py "$task/source/check.py" --vectors "$task/evidence/run01/vectors" --simulation "$task/evidence/run01/simulation" --out 'E:/fft29-review-check-01.json'
& $py "$task/source/audit_reference.py" --reference "$task/reference/b-dynamic-range" --out 'E:/fft29-review-reference-01.json'
```

期望分别得到 SHA-256 全部一致、9 项校验器测试通过、资源/XCI 转录一致、`PASS_SELECTED_FFT29_RTL_ONLY`、`PASS_ARCHIVE_INTEGRITY_AND_REAGGREGATION_ONLY`。最后两项是重新比较保存的数据，不是新的 RTL 运行或重算 B 整链。

## 新建工程重新综合、布局布线及 XSim

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$vivado = 'F:/AMD/2025.2/Vivado/bin/vivado.bat'
$task = (Resolve-Path 'task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01').Path
& "$task/source/run.ps1" -Python $py -Vivado $vivado -OutRoot 'E:/fft29-review-run-01'
```

该入口依次检查测试器、校验/打包归档输入、创建新 29 位 IP、OOC 综合、核布局布线、XSim、逐整数码对照。失败时保留输出目录，换新目录重跑；不删除失败记录。Vivado 报表在 `project/`，仿真原始结果在 `project/fft29_budget.sim/sim_1/behav/xsim/`，最终比较在 `check.json`。

本轮实际逐条执行了构建、仿真及检查命令；总入口 `run.ps1` 通过 PowerShell 语法检查，未另外重复运行一整轮。最新 `prepare.py` 在新位置再次生成的 inputs.mem、expected.npy、job-count.mem、selection.json 与本轮运行输入逐字节相同。最初预备的 job-count.txt 也保留，它只是改为 .mem 导入前的同内容副本，不是另一次仿真。

首次执行对应的独立步骤如下（本轮实际使用 `E:/ss-fft29-build-01`，向量与日志在任务包 `evidence/run01`；日志记录了完整绝对路径和执行时刻）：

```powershell
& $py "$task/source/prepare.py" --reference "$task/reference/b-dynamic-range" --out 'E:/fft29-review-vectors-01'
& $vivado -mode batch -notrace -source "$task/source/build.tcl" -log 'E:/fft29-review-build01.log' -journal 'E:/fft29-review-build01.jou' -tclargs 'E:/fft29-review-project-01'
& $vivado -mode batch -notrace -source "$task/source/simulate.tcl" -log 'E:/fft29-review-sim01.log' -journal 'E:/fft29-review-sim01.jou' -tclargs 'E:/fft29-review-project-01' 'E:/fft29-review-vectors-01'
& $py "$task/source/check.py" --vectors 'E:/fft29-review-vectors-01' --simulation 'E:/fft29-review-project-01/fft29_budget.sim/sim_1/behav/xsim' --out 'E:/fft29-review-bitexact01.json'
```

`build.tcl` 必须先于 `simulate.tcl`。`run.ps1` 已统一处理上述步骤。XSim 在 TB 终止前可能缓存 CSV/日志，不能按运行中的零字节长度判断没有输出。

## 可选：从固定 B 提交重新获取同一批原件

```powershell
git clone --depth 1 --filter=blob:none --no-checkout --single-branch --branch task/member-b-fft-bitexact-01 https://github.com/TophBeifong1744/Competition_fpga.git E:/fft29-review-B-input-01
# 若分支已推进，先保证本地含明确的 bff45e7bbedab321fc4815e1432f1575c750edc4，不能用新 HEAD 替代。
& $py "$task/source/archive_inputs.py" --repo 'E:/fft29-review-B-input-01' --out 'E:/fft29-review-B-reference-01' --fetch
```

脚本固定 B SHA、选取案例 ID、校验 Git blob SHA-1 和 B manifest SHA-256，逐个取对象，不触碰 B 工作树/index。网络失败单独保留，不能把缺失对象或 HTTP 错误页当输入。实际完整获取记录见 `reference/b-dynamic-range/provenance.json`。

## 比较层次

- B 原件：本包选定的 Git blob、NPZ 和源文件字节按 SHA-256 精确核对；压缩 frames 解压还与 B 记录的原 JSON 字节哈希核对。
- RTL：比较有符号整数实/虚码、job/bin 次序与 overflow，不要求 CSV 换行风格或容器格式相同；原输出 CSV 以 gzip 无损封存，解压后的 SHA-256 单列保存。
- 新综合/P&R：比较配置、资源和时序是否支持结论；日志、路径、日期、DCP 或布局结果不要求逐字节一致。若出现数值差异，应记录实际环境和差异，不用“工具退出码 0”掩盖失败。
- 公共右移：独立软件 RNE 检查只验证归档适配关系，不是适配 RTL 通过。没有 IFFT29 或整链的新通过结论。
