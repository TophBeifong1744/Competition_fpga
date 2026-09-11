# B FFT 位精确验证 01：固定向量模型对照

日期：2026-09-10。状态：第一步通过，B 新成果待 A 复核，未合入或推送。本次不是对 A 整包的新 XSim/综合复核批准。
工作分支 task/member-b-fft-bitexact-01，基于 A 准确提交 ac0ff38e954dac094fd84e28b329dcb24dded7fb；A 的 main 基线为 9878ccafdda6cd5a522cc9de95c1277bcee70f08。旧 B 审核分支不追加本研究。

## 已完成

1. 执行 A verify.py：21 个文件哈希匹配，重新生成输入码完全一致，本机浮点 reference 最大差为 0、文件字节也一致；重算 22 次变换/22,528 个输出及周期预算通过。新输出在 evidence/archive-run01，不改 A 封存包。
2. 使用本机 Vivado/Vitis 2025.2 配套 AMD xfft_v9_1 位精确 C 模型，对相同输入计算 6 FFT + 16 IFFT（最后一次对应 A 背压测试的数学输入）。逐项比对 A 归档 XSim 输出的 job、自然索引和有符号整数码。
3. 22,528 个复数样点、45,056 个分量整数码零差异，22 个模型 overflow 均为 0。模型不模拟 AXI 背压周期；不能将数学对照称为新的协议仿真。

实际环境 Windows 11、CPython 3.12.14，模型 DLL 和头文件 SHA、模型参数和输入证据 SHA 见 comparison.json。不分发 AMD DLL、头文件或加密 HDL，复跑使用各自合法安装。

## 关键标度与预算采用

- IP 应用输入是 S25F23，但供应商 C 模型固定点 API 使用 [-1,1) 的 Q1.24 表示。送入模型必须是 signed25_code/2^24，返回乘 2^24 恢复整数码；应用解释仍 code/2^23。此处不改变 H1 的 pcm/2^23。
- 每级右移 1，共十级。前向是 DFT/1024；逆向是标准 IFFT，不再额外 /1024。FFT 互谱相对旧未缩放频谱为 2^-20；原 epsilon 的对应值也须缩放，后续不能简单量化成 0 或直接改阈值。
- IP 溢出应整帧拒绝；不能假设 IP 内部饱和。自写窗乘/转换的舍入、饱和与帧状态另建明确模型。本次正常向量没有验证故意溢出及恢复。
- 采用 A 目标场景：100 MHz、21 次变换实测调度 155,526 周期=1.55526 ms；规划 168,000 周期=1.68 ms，剩余 898,666 周期为未验证模块及停顿/安全余量预算。不是全链路延迟。
- A 综合值 6 DSP、6 RAMB18（3 Tile）、1292 LUT、2148 FF 为单核 OOC 来源结果；本机未重新综合，不能作为整机资源/布局布线/实板通过。外部缓存还需全谱共轭装配、端口并发、倒数/LS/FIFO 等预算。

## 原始失败和文件字节

首次 cmodel-run01 找到主 DLL，但 Windows 未找到其依赖，加载失败，未产生数值结果。使用进程内 os.add_dll_directory 指向同安装 fpo_v7_1 后成功，没有改系统 PATH 或安装。失败说明保留于该目录。
cmodel-run02 为首次成功；追加配置防错校验、执行脚本及依赖 SHA 记录后在 cmodel-run03 再跑。
模型 CSV 使用 LF，A 原文件使用 CRLF；整数码全部一致不等于文件字节一致，comparison.json 独立记录 output_file_bytes_equal=false。A 原始文件不转换、不重封。

## 复跑

仓库根目录，输出路径必须不存在：

```powershell
$py = 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$pkg = 'task-packages/PKG-B-ALG/tasks/fft-bitexact-01'
& $py -B task-packages/PKG-A-ACQ/tasks/fft-ip-budget-01/verify.py --out "$pkg/evidence/archive-new"
& $py -B "$pkg/compare_cmodel.py" --dll D:/AMD/2025.2/win64/tools/fft_v9_1/libIp_xfft_v9_1_bitacc_cmodel.dll --dependency-dir D:/AMD/2025.2/win64/tools/fpo_v7_1 --out "$pkg/evidence/cmodel-new"
```

其他机器替换 Python/AMD 安装绝对路径。不要用自行编写的浮点 FFT 冒充供应商位精确模型。compare_cmodel.py 检查固定来源哈希与支持的合同，任何变化需要重新核查。

## 下一步

先做窗乘积最近偶数舍入/饱和到 S24F23 再符号扩展到 S25F23 的整数模型；生成新种子与边界向量，经同配置新 XSim 与 C 模型逐码比对。随后接入共轭补全、PHAT 模长/倒数及 epsilon 标度，逐级统计误差和溢出/无效帧，再检验角度与跟踪离散变化。
以上均未由当前固定 22 向量代替；本轮不是独立验证集性能、完整定点链、默认算法替换、H2/H3 或实板验收。完整 A 交付复核仍需新综合/仿真证据，本次未合并 A 分支。
