# B 加窗整数模型与新 FFT 向量验证

日期 2026-09-10；独立任务包 fft-window-02。候选配置来源为 A 提交 ac0ff38e954dac094fd84e28b329dcb24dded7fb，FFT v9.1 rev15、1024 点、25 位分量、24 位旋转因子、Radix-2 Burst、每级移 1 位、自然顺序、convergent_rounding。不修改 A 封存包、默认算法、跟踪器或实际硬件工程。

## 本步实现

- window_model.py：对称 Hann（与原 np.hanning 一致，非周期窗），量化为 U18F17；S24F23 乘窗，精确整数乘积移 17 位并最近偶数舍入，限幅到 S24F23，然后保留整数码符号扩展到 S25F23，绝不左移。
- run_vectors.py：以 Fraction 独立验证 845 个算术案例；拒绝 5 类不合法输入/频谱案例；生成新的整数输入与 AMD C 模型黄金输出。C 模型 API 使用 code/2^24，应用仍为 code/2^23。
- conjugate_complete：513 个单边频点补成 1024 点，DC/Nyquist 要求虚部为零，先检查共轭取负是否超出 signed25，不能悄悄溢出。
- check_simulation.py：逐项验证 job/index/输出码，任何一个码不同都失败；另核对测试台成功标记、输出个数、TLAST/状态/背压检查结果与周期记录。不使用 A 的 16 码浮点冒烟容差作为逐码标准。

source-snapshot 中 build.tcl、simulate.tcl、tb_fft.sv 原样来自 A。cmodel_abi.py 是 B 上轮模型适配器快照，只导入 ABI 类型；不运行它的历史向量入口。不包含供应商 DLL、加密 HDL 或仿真库。

## 向量和误差解释

前六次为加窗后的实 FFT：零、负满量程 DC、正负满量程交替、中心冲激、37.25 bin 单音、新随机种子 2026091101。后十六次为独立共轭频谱 IFFT，种子 2026091200..2026091215；最后一次还有输入间断/输出背压。
这些逆向频谱只是有界整数测试数据，并未经过 PHAT；不是“真实 PHAT 结果已验证”。同样，前六帧不是同一场景六个麦克风，不能据此评价定位性能。

加窗模型有效输入 |pcm|≤2^23、窗系数范围 [0,1]，数学上乘窗不增幅，正常输入不会触发饱和；本批次饱和次数为 0，不能作为超范围恢复已覆盖的证据。越界 PCM/窗系数直接拒绝。显式限幅保留为算术出口防护，尚未验证对应窗 RTL。

Hann 系数量化误差上界为 2^-18；乘满量程 PCM 加末端舍入总误差界为 32.5 码。本批次观测最大 31.89433994 码（约 3.80e-6 归一化幅度）。这项误差来自窗量化，独立于 FFT 的位精确一致性，不代表已批准最终窗宽。
模型 FFT/IFFT 相对双精度同输入参考的最大分量误差为 1.456498865 码。共轭频谱 IFFT 最大虚部残余为 1 码：不隐去、不强制置零，后续实相关输出策略仍需验证。以上是本批次观察值，不是通用验收阈值。

## 复跑命令

在仓库根目录使用 Python 3.12 + NumPy，以及合法 Vivado 2025.2。所有输出路径必须是新的短英文目录，勿覆盖旧结果。替换各自安装路径：

```powershell
$py = 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$vivado = 'D:/AMD/2025.2/Vivado/bin/vivado.bat'
$pkg = 'task-packages/PKG-B-ALG/tasks/fft-window-02'
& $py -B "$pkg/run_vectors.py" --dll D:/AMD/2025.2/win64/tools/fft_v9_1/libIp_xfft_v9_1_bitacc_cmodel.dll --dependency-dir D:/AMD/2025.2/win64/tools/fpo_v7_1 --out F:/NUEC/fft-window-vectors-new
& $vivado -mode batch -nojournal -log F:/NUEC/fft-window-build-new.txt -source "$pkg/source-snapshot/build.tcl" -tclargs F:/NUEC/fft-window-build-new
& $vivado -mode batch -nojournal -log F:/NUEC/fft-window-sim-new.txt -source "$pkg/source-snapshot/simulate.tcl" -tclargs F:/NUEC/fft-window-build-new F:/NUEC/fft-window-vectors-new
& $py -B "$pkg/check_simulation.py" --vectors F:/NUEC/fft-window-vectors-new --sim F:/NUEC/fft-window-build-new/fft_budget.sim/sim_1/behav/xsim --log F:/NUEC/fft-window-sim-new.txt --out F:/NUEC/fft-window-comparison-new.json
```

归档的整数输入、窗系数与黄金输出是本轮精确对照依据。跨环境重新生成三角函数/窗时应核对输入 SHA，若不同要保留并说明，不能改旧输入清单。

## 边界和后续

结果与原始日志见 evidence，执行结论见 RESULT.md。本步只验证 Python 加窗整数模型的规则，以及这些新输入下 FFT RTL 与供应商模型的一致性；没有加窗 RTL、完整 PHAT/倒数/阈值、定位/跟踪或实板验收。100 MHz 是模块目标；OOC 综合不等于整机布局布线通过。
首次受限 Vivado 运行 Tcl appinit 失败；原始失败日志保留。随后使用独立目录重新运行同一构建脚本，未重置 TclStore、未修改全局 PATH 或安装。
交由 A 复核后再由 A 合入。下一步是确定 PHAT 模长/倒数和低能量 epsilon 的可表示方案，以及无效帧向跟踪器的传递语义。
