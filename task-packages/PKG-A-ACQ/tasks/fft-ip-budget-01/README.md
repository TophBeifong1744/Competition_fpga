# A 最小 FFT IP 配置与周期、资源评估

版本：a-fft-ip-budget-0.1；2026-09-10。状态：**A 实验完成，待 B 复核；不是 H2/H3 通过。**

基线 main：`9878ccafdda6cd5a522cc9de95c1277bcee70f08`。对应 B 的 input-boundary-adoption-01；不修改其已批准配置、默认算法、其他成员内容或实际 one 工程。

## 1. A 的决定

选用**一个共享的 FFT v9.1（revision 15）、1024 点 Radix-2 Burst** 作为下一轮位精确研究的具体工程候选，目标 100 MHz。25 位输入/输出分量、24 位旋转因子、scaled、convergent_rounding、自然顺序、nonrealtime，启用复位、索引和溢出报告。固定点接口按应用 S25F23 解释，不改变 H1 整数交换协议。

这是已生成和仿真的最小 IP 配置，不是接入整机或最终数制批准。B 可据此开展逐级数值验证，无需等实板；不得仅用本次浮点误差结果宣称 bit-exact。

权衡：共享核实测吞吐有余量，暂不增加并行 FFT 或更换大吞吐架构。选 B 的缩放存储路线继续验证，增长参考候选保留为离线对照，不直接实例化为同一个 IP。

## 2. 已有证据

| 项目 | 实际结果 |
|---|---|
| 工具/器件 | Vivado 2025.2 build 6299465；xc7z020clg400-2 |
| IP | xilinx.com:ip:xfft:9.1；revision 15，来自实际配置导出 |
| 无停顿配置握手至最后输出 | 含首尾 7,402 周期 |
| 首个输入至首个输出 | 相差 6,377 周期 |
| 测试调度器串行配置间隔 | 7,406 周期，含测试调度间隙；不是证明最小 II |
| 仿真 | 6 FFT + 15 IFFT，另加 1 次输入间断/输出背压，共 22 次、22,528 个复数输出 |
| 检查 | 输出计数、自然顺序索引、TLAST、溢出状态/事件、输出背压稳定性通过 |
| 浮点参考最大分量误差 | 1.302315301 个输出码；RMS 0.149785757 个码 |
| 误差检查门限 | 预设 16 个码，仅本轮工程冒烟检查，不是算法验收门限 |
| 综合资源 | 1,292 LUT、2,148 FF、6 DSP48E1、6 RAMB18E1（3 个 BRAM Tile） |
| 综合后时序估计 | 10 ns 约束下 WNS +6.940 ns，TNS 0；OOC 未布局布线，不能当整板时序通过 |

向量含零、冲激、DC、单频、固定种子宽带随机及正负近满量程交替；前六次输入为实数，后续也含复数输入，核对正反方向与 1/1024 比例。参考使用独立 Python 浮点 radix-2 变换，不是 AMD 位精确 C 模型。未覆盖任意输入的最坏误差、任意背压、连续最小 II、复位中断帧或完整 PHAT/定位链。

## 3. 提供给 B 的数制与接口合同

详见 contract.json 和 evidence/run01/ip-properties.txt、ss_fft.xci。

- 实际输入/输出 AXI TDATA 为 64 位：实部 [24:0]，虚部 [56:32]，每个分量按 32 位槽右对齐；输入槽高位符号扩展，输出只取有效 25 位再符号扩展。顺序为自然序，输入 TLAST 只在第 1024 个握手点置位。
- 窗后候选 S24F23 数值符号扩展为 S25F23，不左移；窗乘积的舍入/饱和位置仍由 B 给出。IFFT 输入 PHAT 分量也按 S25F23；完整实序列 IFFT 须正确共轭补全、处理 DC/Nyquist，不能直接把 513 点送入本 1024 点复核。
- 正反变换各十级，每级右移 1，总右移 10。24 位配置字的 bit0 为 FWD_INV，bits[20:1] 为 SCALE_SCH，各两位从低位对应起始级；FFT `0x0AAAAB`，IFFT `0x0AAAAA`。配置必须握手后再发对应帧。
- 因此前向输出物理量为 DFT(x)/1024；逆向为正指数和/1024，与通常 IFFT 的 1/N 一致，**不能再除一次 1024**。本配置不是前向不缩放的浮点 FFT。
- 如果原浮点 PHAT 用未缩放 FFT 的互谱，则本互谱缩放为原来的 2^-20。epsilon=1e-15 的物理对应也须同步缩放，不能直接量化成零。模长/倒数、阈值数制、低能量拒绝、公共输入增益仍待 B 设计并复核。
- IP 的 convergent_rounding 选项不等于项目所有算术节点已统一最近偶数舍入；后续需对实际 IP 模型逐码验证。
- **IP 溢出时拒绝整帧，不继续交给定位/跟踪当有效帧。** 本轮正常向量未报告溢出；未验证故意溢出恢复流程。不能宣称 IP 内部实现饱和，也不能在发生内部溢出后靠末端饱和恢复正确值。B 的“饱和并计数”规则需区分自写算术和供应商 IP，统一明确无效帧语义。

十级各移一位仅为本候选；不能推广为任意满量程复数输入的无溢出保证。本轮保留 1 位应用幅度余量，PCM 公共增益和 PHAT 单位模约束仍须明确。

## 4. 周期与资源预算

六麦 Fs=48 kHz、hop=512，每 hop 在 100 MHz 下保守取 1,066,666 周期。

- 实测串行 21×7,406=155,526 周期，即 1.55526 ms。
- A 规划每次变换 8,000 周期、21 次共 168,000 周期（1.68 ms）。该服务槽只在输入连续、输出及时接收和有界调度条件下使用；不是任意背压的实时保证。
- 尚余 898,666 周期，需覆盖窗口、频谱缓存读写/共轭装配、互谱/PHAT、峰值、几何/秩、控制和停顿，再留安全余量。不能把“剩余”当这些模块已经验证。
- 单 FFT 核规划额度：8 DSP、4 BRAM36 等效 Tile、2,000 LUT、3,000 FF；实际综合分别为 6、3、1,292、2,148。该额度是 A 的设计约束，不是器件供应保证或最终整机占用。
- B 原 75,317 B packed / 84,364 B 字节对齐是部分外部缓存。当前核内部另外使用 6 RAMB18；不要把 BRAM 含校验位容量当作可用数据字节直接相加。输入全谱装配、输出缓存、端口并发、LS/倒数/FIFO 与持续音频缓冲仍需补齐，整机 RAM/DSP 分配保持 null。
- 实际综合器件报告可用 220 DSP、140 BRAM Tile；减去单核不等于其他模块都可任意使用。未用 one 工程资源报告为整机余量背书。

## 5. 复现

包内仅自写脚本、配置和证据，不分发 AMD 加密 HDL、仿真库或 DLL。使用者需自行安装合法 Vivado 2025.2 及对应器件支持。建议新短英文绝对路径，不覆盖已有输出。

仓库根目录，用 Python 3.12 和 **2025.2 的完整 vivado.bat 路径**（本机 PATH 默认曾指向 2018.3）：

```powershell
$python = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$vivado = 'F:/AMD/2025.2/Vivado/bin/vivado.bat'
$pkg = 'task-packages/PKG-A-ACQ/tasks/fft-ip-budget-01'
& $python -B "$pkg/verify.py" --out E:/ss-fft-verify-new
& $python -B "$pkg/vectors.py" --out E:/ss-fft-vectors-new
& $vivado -mode batch -nojournal -source "$pkg/build.tcl" -tclargs E:/ss-fft-build-new
& $vivado -mode batch -nojournal -source "$pkg/simulate.tcl" -tclargs E:/ss-fft-build-new E:/ss-fft-vectors-new
& $python -B "$pkg/check_results.py" --vectors E:/ss-fft-vectors-new --sim E:/ss-fft-build-new/fft_budget.sim/sim_1/behav/xsim --out E:/ss-fft-new-result.json
```

第一步仅验证归档、重新生成输入/浮点参考并重算历史仿真输出；后三步才是新 IP 综合和 XSim 复现。预期生成 properties、XCI、模块资源/综合时序报告，仿真生成 outputs.csv、cycles.csv，检查输出 PASS_IP_PROBE_NOT_H3。

本轮初始失败：受限进程无法加载 Tcl appinit，带 .codex 路径也失败；未改全局安装，在授权的短路径隔离工程运行后解决。随后 add_files 对含空格路径的列表解析失败，改成 Tcl list 后重跑通过。实际成功原始日志见 evidence/run01；OOC HD.CLK_SRC 未指定及本机无关板库警告不隐去，不宣称布局布线或全局环境全部无警告。

## 6. B 的下一步与验收边界

B 先复核本包固定 SHA，复跑配置、仿真与预算；随后建立对应该 IP 的整数输入和模型，验证窗口接入、正反比例、逐级误差/饱和或无效帧、PHAT 阈值映射、位宽与离散跟踪副作用。误差限与异常策略需双方确认，不能沿用本包 16 码冒烟门限当整链路标准。

本轮完成 A 的具体 IP 配置和模块级工程预算证据。**未修改主线算法或实际 BD；未通过 B 独立复核、完整定点、H2/H3、布局布线或实板。** 不要求用户再手工搭一个相同 FFT 工程才能开始 B 的数值研究。
