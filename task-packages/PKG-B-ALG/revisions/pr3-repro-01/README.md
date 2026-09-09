# PR #3 逐项整改与复现说明

日期：2026-09-09。请求来源：[A 的请求修改](https://github.com/TophBeifong1744/Competition_fpga/pull/3#pullrequestreview-5150301753)，审核对象 `25a6257fe3136b058cefa06e86fde0f3c8dd8dff`。
本轮仍仅申请六麦合成离线研究材料入库；由 A 重新复核，不自行合入 main。

## 1. 补齐 run.log 和清单验收

问题：`stable-wrong-01/files.json` 声明的原日志未提交。

处理：在作者本地 `F:/NUEC/task-packages/PKG-B-ALG/research/stable-wrong-01/run.log` 找到原文件；按字节补交，未根据结果反向编造日志。SHA-256 为 `fb1e82e7e76c53706568e19883ba46ffd61cae4b0ee1e3f163c75c66713121fb`，与原清单完全一致。该文件被通用 `*.log` 忽略规则匹配，故此次使用精确路径强制加入 Git；没有修改全局或旧包忽略规则。

修改文件：新增原日志；新增 `common.py` 的 `verify_entries/verify_package`、`verify_release.py`、`test_revision.py`。六个原 `files.json` 与 `fixed-files.json` 不改写。修订产物另有本目录 `files.json`。

验证命令（本包根目录）：

```powershell
python -B revisions/pr3-repro-01/verify_release.py
```

实际结果：六个清单分别 19、34、26、26、26、11 项，共 **142/142** 文件存在且 SHA-256 匹配；633 个去重冻结路径继续受检。新增测试实测缺失日志、篡改字节均导致失败，不能将清单存在等同于清单通过。

## 2. 数值复现与输入完整性分离

问题：旧审计用 `arccos(dot)` 对近零夹角重算并要求绝对 `1e-8°`，且将重建输入的哈希不同混同为可移植性问题。

处理文件：`common.py`、四个 `audit_*.py`、`stable_rerun.py`、`run_all.py`、`probe_input_environment.py`。`source-origins.json` 记录各修订脚本所依据的原文件及原 SHA-256。原脚本、原数值结果和协议完整保留，修订版没有改写默认算法的计算或任何分类门限。

验收分三层：

1. **落盘完整性**：原始证据、算法源码、协议、清单、历史评审快照均严格 SHA-256。历史评审再核对 Git blob SHA-1。哈希失败就是失败。
2. **重算浮点量**：审计使用 `atan2(norm(cross(u,v)),dot(u,v))`，先显式归一化；仅将重算结果与旧 arccos 记录比较时使用浮点误差界。以 binary64 `epsilon=2^-52`、归一化与三项点积的保守 16 次舍入预算，令 `delta=16*epsilon/(1-16*epsilon)`；对新角度的余弦取 `[cos(theta)-delta, cos(theta)+delta]`（截到 [-1,1]），映射回角度区间，另设 `1e-10°` 的角度转换下限。零角附近预算上界约 `4.829673e-6°`，离开病态区间会迅速缩小；并非为所有角度统一放宽到该值。测试证明近零 `1e-4°` 差异及 5° 附近 `1e-6°` 差异仍被拒绝。时延等沿用绝对 `1e-8` 且去掉隐含相对宽容；每一比较逐项检查并记录最大差异、对应旧值/新值与允许界。
3. **离散量**：有效性、类别、频带索引、共同有限麦对、样本键及次序、跳过条件、范围归属、fresh/无效计数精确一致。连续量容差不参与任何实际分类决策；分类一旦不同，即使浮点量接近也失败。

### 明确的重建环境，而非无依据接受波形差异

本轮选择请求中允许的“明确可复现环境”路线，**不宣称跨任意环境波形数值等价**。支持并实跑的输入精确重建配置是 Windows 11 x86-64、CPython 3.12.14（MSC v.1944）、NumPy 2.3.5、scipy-openblas 0.3.30 的原二进制，AMD Family 25 Model 97 CPU，NumPy 默认启用的 AVX512/FMA 路径，无 `NPY_DISABLE_CPU_FEATURES` 覆盖。仅 Python/NumPy 的版本号相同不充分。

完整处理器、SIMD dispatch、编译配置、NumPy 原生模块和 DLL SHA-256、Python 可执行文件 SHA-256、环境变量，见 `evidence/attempt-01/environment.json` 和 `evidence/integration-01/environment.json`。哈希仍是每次运行的最终约束，不能仅因环境名相同就跳过检查。可先运行：

```powershell
python -B revisions/pr3-repro-01/probe_input_environment.py --out <新的探测目录>
```

实际结果：四个审计分别严格核对 10、8、8、8 次完整输入重建，stable 再严格核对 26 组；每组 input/target/noise/RIR 四项均匹配历史哈希。stable 还独立重组 target+noise，并保留目标/噪声随机流及同帧活动支撑检查。输入哈希列表见各 `differences.json`，不是只写一个 PASS。

受控替换 SIMD 路径（禁用 AVX512/AVX2/FMA3）后，同一 `tone900__front__early_late`、seed 2026091500 的 input/target 哈希不同、noise/RIR 相同，新入口实际返回非零并记录 `UNSUPPORTED_EXACT_INPUT_ENVIRONMENT`；见 `evidence/alternate-cpu-attempt-01/`。这是本机受控实验，不冒充 A 的机器或断言已锁定 A 的全部差异来源。由于历史完整波形没有保存，该路径没有逐样本参考，不计算虚假的波形最大误差，也不能宣称那些波形已证明相同；须使用上述精确重建环境。后续如要支持其他环境，应先交付有可靠历史哈希来源的完整波形参考或另一套已验证数值执行环境，不能把错误转为警告。

### 实时重算结果

| 比较量 | 本次最大绝对差异 |
|---|---:|
| subband direction_spread | 8.8076722131e-11° |
| leave-band-out max_angle_change | 1.7075472925e-6° |
| effective max_angle_change | 1.9090959104e-6° |
| 上述两包最大时延变化 | 0 samples |
| stable 对照 cone_deg | 2.4868995752e-14° |
| stable 对照 error_deg | 4.6759803668e-10° |

这些差异均在各自逐值误差界内，离散结果无差异。旧 leave/effective 审计在本机原 SIMD 环境也实际运行并通过，日志见 `legacy-attempt-01`；不把 A 在另一环境观察的失败伪造成“本机也失败”。上面的受控输入失败及下面的 main 冻结失败均保留真实 traceback。

## 3. 历史冻结与当前评审分离

问题：旧冻结链指向包根可追加 `REVIEW.md`，正常保留 main 上 A 的评审即失败。

处理文件：`history/REVIEW.md`、`history.json`、`common.py`、五个 `final_*.py`、`stable_tests.py`。旧六包文件和清单继续不可变；新入口对唯一明确的 `REVIEW.md` 历史引用，使用 `history.json` 指定的不可变快照校验。其源提交为 `25a6257`，原路径为 `task-packages/PKG-B-ALG/REVIEW.md`，Git blob 为 `e4cbf5b79b17853646ccfe2d62e840bbdc6155c4`，SHA-256 为 `5190a33d3267ca9fb96fe981905d5f9196415657256a3905fb41ae2e129c91c7`。遇到其他历史 REVIEW 哈希会拒绝，不做通配豁免。

所有非 REVIEW 冻结路径仍读取当前对应文件并严格校验原哈希。新入口不覆盖、不回退、不向历史 snapshot 混入当前评审；当前 REVIEW 哈希单列记录，不将其当作算法证据。原 `final_check.py` 保留用于复现旧失败，本次受支持的验收命令是 `verify_release.py` 和 `run_all.py`，不是旧入口。

实际集成基线：`1ec105f609ac52d7b97d3245a90dc212591c1cfa`（包含最新 PR #4），测试修订提交 `018fd95694bf742057428e5af74078be06a54c6d`。在独立工作树试合并，无冲突，main 既有文件无修改/删除。当前 REVIEW 与 main blob 逐字节一致，SHA-256 为 `ced3b345947ff9f41649eaeb3d4b4383899b29a7ac0f3dab19211ae7524df650`。旧 tonal final 在此副本中真实报 `AssertionError: REVIEW.md`，新入口通过；见 `evidence/main-compatibility/`。

## 4. 新运行、命令与结果

在本包根目录，使用上述精确重建环境：

```powershell
python -B revisions/pr3-repro-01/verify_release.py
python -B revisions/pr3-repro-01/run_all.py --out <新的完整输出目录>
```

脚本拒绝已经存在的输出目录。子进程分别加载六包，避免同名 `study/features` 模块污染。每个阶段保存真实命令、退出码、日志、结果和差异；一个阶段失败不能从旧 PASS 补齐。`final_*` 对旧证据做一致性核查，同时 **run_all 强制再次运行四个 live audit 和 stable 重跑**，不会以旧 audit.json 代替它们。

两次完整执行分别保存在 `evidence/attempt-01/`（独立修订副本）和 `evidence/integration-01/`（保留 main 的集成副本）。逐阶段结果见各自 `run.json/stages.json`；六组回归依次为 **170、172、173、173、173、172 项通过**，其中每组都包含原 167 项；另外修订机制 7 项测试通过。五个 final、四个 live audit、stable 完整同帧重跑均通过。实时审计仍按原范围重算全部落盘分类/统计，并重建原审计所规定的输入子集；没有声称全量重跑前五包全部声学试验。

stable 重跑重新选出全部 563 个候选，并计算 26 组输入、2,252 个同帧对照；逐项比较 cohort/controls/summary，样本键、计数、布尔量、类别与原记录完全一致。

| 对照，分母均 563 | 有效 | 仍误入范围 | 误入且 stable |
|---|---:|---:|---:|
| 原输入 | 563 | 563 | 563 |
| 去噪声 | 563 | 185 | 130 |
| 去反射 | 549 | 309 | 297 |
| 同时去掉两者 | 563 | 0 | 0 |

去反射的 **14 个无效** 单列，未算作正确。候选 **563＝317＋246**；所选候选同一时刻的 fresh 为 **182**，上一包全批范围外 fresh 为 **205**，三者不是同一分母。未重跑对照跟踪状态机，不宣称 fresh/HOLD/捕获延迟有改善。

重算后的 cohort、controls、summary 因稳定角度计算与旧文件字节不同，原文件保持不动；字节比较、逐字段最大数值差异及精确离散比较见 `stable/result.json` 与 `stable/differences.json`。差异没有通过覆盖历史结果消失。

## 未解决的范围限制

- 输入精确重建有上述环境边界，另一 CPU/SIMD 路径不能凭同版本号或相近估计结果认定历史波形相同；当前不提供任意环境重建的豁免。
- 原五包全量试验未全部重跑；已经运行其适用回归、实时审计、清单核验和指定输入子集，stable 26 组控制全跑。
- 本轮修订的是验证交付，未将研究候选变成默认，也不新增四麦研究、实板或 H2/H3 通过声明。A 原有批准只覆盖前轮；此次仍待 A 再复核。
