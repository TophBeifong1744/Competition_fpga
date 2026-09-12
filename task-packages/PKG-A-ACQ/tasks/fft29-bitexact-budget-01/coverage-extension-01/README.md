# FFT29 剩余归档向量覆盖：coverage-extension-01

最新状态：拓芙已完成817-job XSim，136个新增case逐码全部一致；与历史60帧合并为196/196。
详见[RESULTS.md](RESULTS.md)、[复现说明](REPRODUCE.md)和[交付回报](HANDOFF.md)，仍待B独立复核。
以下为准备操作说明；准备阶段原文和哈希已通过PREPARATION-HISTORY.json保留，不抹去当时未运行的状态。
不提交、推送或自行合入；完成后交“拓芙工作执行”检查交付并提交给 B 复核。

## 本轮做什么

原批准输入提交 bff45e7bbedab321fc4815e1432f1575c750edc4 不变。
用户给定 main 基线 e670eef5de66e85981db8880bee6d41d9afb3a18；
当前实际 HEAD 以 evidence/input-audit-01.json 为准，须是该基线后代且旧 FFT29 任务树不变。
其他任务 skill/pynq-overlay-dma-validation 未提交修改不属于本轮，保留不碰。

从旧 selection.json 与 check.json 的准确 case ID 求差集，
只准备余下 136 帧，每帧六个离线研究通道，816 次唯一 FFT。
额外重放本轮第一项 case001/ch0 一次，保留旧输入间隙/输出背压检查，共 817 次。
这不是四麦采集扩为六麦，也不是重跑全部 196 帧。
旧 60 帧/361 次属于历史；新 136 帧没有运行成功前不得合计称 196 帧通过。

原已批准 60 帧的依据：
../evidence/run01/check.json 及 B closeout-01/a29-review-01/README.md。
旧资源/时序引用 ../evidence/run01/reports/，本轮不做新资源预算、综合或布局布线。

## 最小适配与复用

- source/tb_fft29.sv：仅把输入存储 361×1024 扩为 817×1024、
  预声明作业数改为817、超时600万改为1200万周期。
  100MHz、0x0AAAAB、TLAST/index/overflow/未知值/背压保持检查均不变。
- source/check.py：只把成功标记中的361改为817；原 compare 逐实虚整数码逻辑完全不变。
- source/create_sim.tcl：逐字复用原 build.tcl 的 create_ip/config 配置块；
  只生成仿真支持和打开 XSim，不调用综合/实现，不访问实际 one。
- source/prepare_extension.py：锁定 B Git 树，按 blob ID 与 B SHA-256 检查输入，
  缺件报错、不下载、不重生成声学输入。新输出目录已存在即拒绝。
  复用原 source/prepare.py 的原字节副本，直接 windowed int64 ×16，虚部零；
  golden 直接使用 wide29_raw_fft，未更改 reference25/PHAT/IFFT/跟踪器或公共右移 RTL。
  原打包器附带的软件 RNE 检查保留，不升级为 RTL 结论。
- source/test_extension.py：原9项正负例用在新比较器上，再加4项适配约束检查。
- 旧所有源码/日志/manifest 均不改。本子目录未来使用单独 SHA-256 清单。
  旧 package_manifest.py 严格枚举整个父目录，因此新增子目录后不能直接用它重写旧清单；
  prepare_extension.py 逐项验证旧清单绑定的原文件，同时容许本次新子目录存在。

必要数据只在新的短路径运行目录快照：136个原NPZ、完整帧索引及manifest/packing。
不复制B整套研究包。固定提交来源、哈希和准确case列表保存在input-index.json，
本任务包的本次核对记录在evidence/input-audit-01.json。

## 拓芙的下一大步：准备并运行这136帧的离线仿真

先运行下列准备命令。只生成输入、snapshot和检查记录，不会打开Vivado或启动仿真：

~~~powershell
$fftExt = 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01'
$fftPy = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $fftPy -B "$fftExt/source/prepare_extension.py" --out 'E:/fft29-coverage-01'
if ($LASTEXITCODE -ne 0) { throw '准备失败，保留输出，不启动仿真' }
~~~

应看到 READY_FOR_USER_XSIM_NOT_SIMULATED: cases=136 unique_fft=816 repeat=1 jobs=817。

打开 Vivado 2025.2，在没有打开工程的欢迎界面找到 Tcl Console。
如果打开了 one，先保存并关闭该工程；不要向 one 添加这些仿真文件。
在 Tcl Console 中执行：

~~~tcl
source E:/fft29-coverage-01/source/create_sim.tcl
fft29_coverage_create E:/fft29-coverage-01/project E:/fft29-coverage-01/vectors
~~~

脚本建立隔离的仿真工程，配置保持29位/1024点/Radix-2 Burst/自然序/100MHz不变；
只生成IP仿真支持并启动Behavioral Simulation，停在0ns。
随后在同一 Tcl Console 执行：

~~~tcl
run all
~~~

预期末尾出现 PASS FFT29 archive replay: 817 jobs; TLAST/index/status/backpressure checked。
看到Fatal、报错或超时就停止，保留完整目录和日志。不要更改golden，也不要删除重跑覆盖。
若目录已存在，用新的 fft29-coverage-02 等根目录，并同步替换上面全部路径。

**先把准备输出及仿真末尾发回本任务。** 然后由工程实现指导逐码对照、
保留失败记录、整理原始日志及覆盖合并结果；TB PASS不能替代逐码比较器PASS。
目前没有执行下一段比较命令：

~~~powershell
& $fftPy -B 'E:/fft29-coverage-01/source/check.py' --vectors 'E:/fft29-coverage-01/vectors' --simulation 'E:/fft29-coverage-01/project/fft29_budget.sim/sim_1/behav/xsim' --out 'E:/fft29-coverage-01/check.json'
~~~

易错点：
1. 不运行旧run.ps1/build.tcl总入口，它们会重复综合和布局布线。
2. 不直接复用原361作业TB/比较器；新的仿真必须使用本轮snapshot。
3. IP输入为29位有符号分量，AXI每复数点64位，不改29位成32位。
4. 波形默认只跑很短时间，使用run all；预计仿真时间约60ms，不是程序卡死。
5. 运行中CSV可能缓冲到磁盘，不能拿暂时0字节断言失败。
6. 817是变换次数，不是帧数；其中仅816次属于新增唯一变换。
7. 不点Generate Bitstream，不下载板卡，不接麦克风。

## 验证与交付

XSim、逐码比较、协议检查、覆盖合并和原始日志归档已完成，记录见evidence/run01/。
作者重复归档复查也已完成；当前只待工作执行检查交付、发布新SHA及B独立复核。
准备入口已允许本extension后续提交，但继续拒绝历史FFT29文件变化，原155项逐个核对。

全部逐码一致也只支持该归档前向FFT候选；不代表定位精度、整链定点或H3通过。
