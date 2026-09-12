# 复现与只读复查

环境：Python3.12+NumPy；新仿真另需Vivado/XSim2025.2 SW6299465、xfft9.1rev15。
不需要上板。输出必须为新目录；不要覆盖evidence/run01或E:/fft29-coverage-01。

## 1. 不启动Vivado，核对交付

在准确待审提交的仓库中运行（把路径换成该工作树）：

~~~powershell
$fftExt = 'E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga/task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01'
$fftPy = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $fftPy -B "$fftExt/source/test_extension.py"
if ($LASTEXITCODE -ne 0) { throw '比较器测试失败' }
& $fftPy -B "$fftExt/source/verify_archive.py"
if ($LASTEXITCODE -ne 0) { throw '归档复查失败，保留输出' }
~~~

期望13项测试通过，以及PASS_READ_ONLY_ARCHIVE_RECHECK_NOT_NEW_XSIM：
136个本轮case+60个历史case=196、817个本轮job、1673216码、mismatches=0。
该核对不依赖原E:/fft29-coverage-01临时工程，也不启动Vivado；
需要仓库中B固定提交bff45e7及其数据对象。缺对象直接报错，不能换golden或默默访问网络。

旧155项按原清单逐项验证；准备阶段14项按PREPARATION-HISTORY映射核对旧字节；
新run01的artifact清单和extension的最终SHA256SUMS分别检查。
不要调用父包package_manifest.py write覆盖原清单。

## 2. 新XSim复跑（不是本轮新增第二次仿真记录）

~~~powershell
& $fftPy -B "$fftExt/source/prepare_extension.py" --out 'E:/fft29-coverage-02'
if ($LASTEXITCODE -ne 0) { throw '准备失败，保留输出' }
~~~

准备入口从固定B归档只取余下136帧，原整数windowed左移4位，复用原打包器。
准备失败记录留在该输出目录。若--check-only在创建目录前失败，保留控制台文本。

在空Vivado2025.2会话的Tcl Console执行：

~~~tcl
source E:/fft29-coverage-02/source/create_sim.tcl
fft29_coverage_create E:/fft29-coverage-02/project E:/fft29-coverage-02/vectors
run all
~~~

创建的是隔离仿真工程，不触碰one，不执行综合/布局布线。
实际结束后应有817-job PASS标记；这不代替后面的逐码比较。

~~~powershell
& $fftPy -B 'E:/fft29-coverage-02/source/check.py' --vectors 'E:/fft29-coverage-02/vectors' --simulation 'E:/fft29-coverage-02/project/fft29_budget.sim/sim_1/behav/xsim' --out 'E:/fft29-coverage-02/check.json'
~~~

原始仿真输入和输出会保留。失败时不清理、不修改golden，换新目录前先定位问题。

## 3. 归档新的实际运行

本轮作者实际执行的归档命令如下，**不要直接重跑覆盖该目标**：

~~~powershell
& $fftPy -B "$fftExt/source/finalize_extension.py" --run 'E:/fft29-coverage-01' --out "$fftExt/evidence/run01" --screenshot 'C:/Users/TOPHBE~1/AppData/Local/Temp/codex-clipboard-1cef1e0a-d1b1-4b6b-b0f6-4d9c7014c58f.png'
~~~

新的复核运行应使用独立待审/复核工作树及新的输出目录，并省略或替换--screenshot。
finalize只收集和检查，不启动仿真。每个子命令、时间、退出码、原始输出保存在run01的*-command.json及*.log。
GUI操作没有独立journal；run-origin.json明确区分操作单指令和真正保存的工具命令，
不把推定操作记录伪装成原始journal。用户截图、编译项目列表、工具版本和实际simulate.log共同记录执行来源。

## 检查新文件清单

最终清单由原source/package_manifest.py对本extension首次生成（--package指向本子目录）。
SHA256SUMS.json不记录自身；用户/复核人应只使用check模式或verify_archive，
不要为了通过而重写清单。新增复核证据应放在独立目录并单独管理。

资源/时序只引用原父包报告，未作本轮重新综合/布局布线结果。
