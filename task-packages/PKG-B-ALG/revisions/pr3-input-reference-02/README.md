# PR #3 第二轮剩余阻断：历史输入参考数据

基线提交：df4146af6aab3263209f54bb36ded8693d2d9d90。复核来源：review-5151964188.json。仅新增本目录；已通过的日志、角度比较、历史 REVIEW 兼容实现、默认 PHAT、跟踪器及阈值均未修改。原失败记录保持原样。

## 变更与最小数据评估

新增 12 个去重的 NPZ 文件，总大小 **6,205,843 字节**，只包含无损 little-endian float64 RIR 数组，不包含完整目标、噪声或混合波形。20 个生成参数键映射到这些文件。

导出前在当前支持环境对每项原始生成结果验证 input、target、noise、RIR 四个历史 SHA-256；任一不符即停止，不会登记为可用参考。环境为 Windows 11、CPython 3.12.14、NumPy 2.3.5、AMD Family 25 Model 97，默认进程具备 AVX512。完整环境、动态库哈希、命令、来源源码哈希在 reference/environment.json 和 reference/index.json。NPZ 容器字节 SHA 与解压后的数组 SHA 分别记录；旧 input/target/noise/rir 清单不改写。

覆盖范围由原协议与 live audit 的选择条件派生：narrowband 10 项、subband 8 项、leave-band-out 8 项、effective 8 项；另含 stable 的 26 项原输入及 26 项对应 dry 输入，共 86 个用途绑定、70 个不同的历史清单记录。stable 的 no_noise 使用历史 target，dry_no_noise 使用对应 dry target；原输入和 dry 输入都通过四类历史哈希预检，然后原 stable_rerun 复算全部 2,252 个同帧对照。

读取入口只替换复核进程中 robustness_sweep.make_rir 的数据来源，其他生成步骤和审核函数仍使用上一修订的代码。RIR 的压缩文件字节、数组哈希、形状、类型、有限值、参数键及历史清单绑定全部检查。之后原 common.Differences.input 的四类严格断言照常执行。未声明输入、文件损坏或目标/噪声/混合波形不匹配都会失败；没有按最终计数放行的路径。

## A 可直接运行的命令

先将 PR #3 的最新提交检出到独立工作区；以下在该工作区的 `task-packages/PKG-B-ALG` 目录执行。使用正常 CPU 设置，不需要 AVX512，也不要设置绕过哈希的开关。输出目录必须不存在，避免覆盖之前的记录。

```powershell
$python = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $python -B revisions/pr3-input-reference-02/verify_release.py
& $python -B revisions/pr3-input-reference-02/test_reference.py
& $python -B revisions/pr3-input-reference-02/run_all.py --out revisions/pr3-input-reference-02/evidence/a-intel-run01
```

每条命令应退出 0；若退出非零，保留输出并反馈。最后一条是**剩余阻断专用完整入口**，执行预检、四个 live audit 和 stable 共六个阶段，不冒充上一版 17 阶段全套回归。已经通过的测试/final 实现没有重写。本轮不得继续运行旧入口期待它自动读取参考，旧入口故意保留原行为和失败语义。

如只需快速确认当前环境是否能够严格重建输入：

```powershell
& $python -B revisions/pr3-input-reference-02/run_all.py --stage preflight --out revisions/pr3-input-reference-02/evidence/a-intel-preflight01
```

如果预检仍失败，保留 failure.json、differences.json、environment.json；它们会指明是哪项历史哈希仍不匹配。此时 RIR 方案在该环境不足，必须补充经历史哈希验证的必要中间量或波形，不能改清单或忽略错误。

## 实际测试结果

- 支持环境导出：86 / 86 用途绑定的四类原始生成哈希严格匹配；原输入参考无重新定义。
- 本机禁用 AVX512 的预检：86 / 86 用途绑定严格匹配；无需目标或完整波形文件。
- 同一禁用 AVX512 进程配置下，完整入口六个阶段全部通过：四个 live audit 的输入重建数分别为 10、8、8、8；stable 完成 26 组、2,252 个同帧对照。
- stable 的 563 / 317 / 246、四组 563 / 185 / 309 / 0、有效数 563 / 563 / 549 / 563 一致；逐字段离散结果一致。cohort.json、controls.json、summary.json 与历史文件字节**均不一致**，原有有界数值比较通过；差异记录在 evidence/avx2-live-01/stable/differences.json，未用计数替代逐项比较。
- 7 项新增机制测试通过，包括损坏文件拒绝、重算容器哈希也不能替换历史数组、未声明输入拒绝、原输入断言仍生效，以及完整覆盖/来源检查。
- 旧六包 633 个冻结路径及已有修订清单校验通过。没有重写前两轮失败记录。

本机受控命令使用 `NPY_DISABLE_CPU_FEATURES=AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL`，配置及实际 NumPy runtime 写入每个阶段 environment.json。导出环境与测试环境分别记录。

**环境限制：本机 AMD 禁用 AVX512 不等于 A 的 Intel 环境。**对 A 提供的三个首次失败条件，本机禁用 AVX512 的原始生成仍能匹配历史哈希，未复现 A 的 RIR 差异。evidence/avx2-minimum-01 如实记录该结果，不能据此否定 A 的失败或宣称 A 已通过。小型参考入口的作用是直接提供已验证 RIR、移除对本地 RIR 浮点生成路径的依赖；A 上其他生成步骤是否仍严格一致，由保留的哈希断言判定。

本轮接受策略是历史输入严格相同，不是跨环境波形容差放行。assess_minimum.py 的波形误差仅用于描述本机原生生成与已验证历史重建的差异，包含最大绝对误差、RMS、相对 L2、不同数值个数与规范数组字节相等性；不将该结果套用到 A。NPZ 文件级字节哈希在 reference/index.json，算法输出的离散与数值/文件字节差异在 live 审核结果中分别记录。

## 导出复现与交付范围

在支持历史原始哈希的环境，从任务包根目录执行以下命令导出到全新目录（不覆盖交付参考）：

```powershell
& $python -B revisions/pr3-input-reference-02/export_reference.py --out revisions/pr3-input-reference-02/evidence/reference-reexport01
```

index.json 给出全部参数绑定和来源；reference/*.npz 为参考数据；export.log/export-input-checks.json 保留导出过程。files.json 覆盖本目录交付文件（自身除外）。导出产物的命令路径和环境元数据可能不同；数组必须仍匹配原始历史哈希。

只推送原审核分支 review/member-b-to-a-pkg-b-alg，继续 PR #3，由 A 复核并决定是否合入。本轮不自行合并。范围仍为六麦合成离线研究材料入库，不代表默认算法替换、实板、H2/H3 或四麦主线验收。
