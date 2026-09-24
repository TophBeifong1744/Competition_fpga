# #13 S1 只读组合入口候选

新增 `check_load.py` 对现有 S1 产物做完整只读 load 预检：保留 S1 六秒合同，显式复用已批准 `21c141b223936730c2ce5139624fcedb412adafb` 的启动与命令检查。本候选待 B 增量审；成功只表示 `ARTIFACT_CHECK_PASS_NOT_BOARD`，不授权下载或现场运行。

基线 `7f26cf115b1b57ddede67439921b562274667fd6`；原始诊断读取准确 `7274df873d6a36da8e16ca54f05688d3c7f09689` 的 `E-HANDOFF-20260921.md` 及 `evidence/scene-dependency-20260921-02/`。该诊断确认旧 S1 policy 绑定 `f9572f…`，活动 checker 为 `d2f5de…`，不是换行差异。本增量不修改旧 policy/check_scene/gate、timerfixed 检查器、冻结证据或实际 one/Vitis。

## 检查合同

- 导入前锁定完整 16 文件依赖闭包，包括新增间接依赖 `command_contract.py`、安全/ELF helper、计时布局、链接脚本与参考产物、S1 历史 post 与交付清单。检查快照和实际 CMake 指向的主 checkout 均须匹配，缺项/变更拒绝。
- S1 保留 16I continuous、11I scene、6000000 us / 288000 组、9600000 B archive、64 B 双保护区、DDR 范围及 108/112 B 两种计时池布局。没有套用 timerfixed 的另一应用名、十秒或 480000 组合同。
- 编译与链接显式使用新版 `command_contract`；预期来自冻结 **S1** 命令。另保留全部四条 Ninja 命令、前后 gate 及 build graph 检查，仅允许原已规定的两个独立前置任务互换顺序。
- `verify_startup` 原函数未改，参考为 `8f708e42caf32c1de6f30726298e3edf0e1970b6` 已归档的 `delivery-01/versions/build/four_mic_endurance.elf`，SHA256 `4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6`。不是从本次待检 ELF 复制生成的预期。
- 核对实际源/配置、平台及三份 XSA、88 个 BSP 文件、工具身份、object/ELF/map、历史 pre/post、launch 与 bit/init；所有读入文件结束时再校验哈希。只有 `ninja -t commands`、GCC `--version`、objdump 被调用，子进程限时 60 秒。
- 历史 post 必须与归档 `build-result.json` 原字节一致；历史 pre、policy、verifier、source/ELF/object/map 身份均保留。新记录明确 `new_build_observed=false`、`historical_gate_approval=NOT_GRANTED`，不制造 pre/post、编译时间或批准。

## 首次失败及参考选择

首个实现检查点 `check_load.py=4700c4e484a83d5872f5f92881bfc49ca156ddd6e11cc5a82584a9765c2300d6` 使用另一应用的 timerfixed ELF 比较整个启动段，真实运行退出 1：`Startup vector/reset bytes changed`。失败记录保留在本 checkout `codex_out/entry-adaptation-smoke-01/20260924_114442_load_dba0e3db50/`。

独立架构核对发现两应用 entry 均为 `0x100000`、`_boot=0x1000cc`；208 B 中恰有 9 个 word 不同：6 个 BL 仍指向同名异常处理函数，其地址均增加 `0x3d0`；3 个 literal 仍指向同名 ExceptionAddr，因 S1 BSS 扩大而变为 `0xa3a700/0xa3a708/0xa3a704`。其余字节相同。因此采用已冻结、已独立接收的 **S1 链接像**作为启动参考，继续精确比较全部字节，不屏蔽指令或放宽启动检查。两条实际 objdump 命令、stdout/stderr、退出码及 9 word 对照保留在 `codex_out/entry-adaptation-startup-20260924/`。

B 对 8f708e4 的批准限 S1 实现/历史输入，对 21c141b 的批准限离线修复；两项均不自动批准本组合，也不批准历史安全 gate。

## A 机复核命令

在持有本候选的 checkout 根执行。此命令替代旧 `prepare.py preflight` 的预检调用；不要再把旧入口作为当前 S1 放行依据。`python` 应为已安装的 Python 3.11+，实际作者使用 3.12.14。工具根是显式参数，未把绝对可执行文件路径写入新运行配置。

```powershell
$entry = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/entry-adaptation-20260924'
$records = Join-Path (Get-Location) 'codex_out/s1-load-review'
python -B "$entry/check_load.py" --stage load `
  --app 'F:/College/verilog_digital_system/Vitis/four_mic_endurance' `
  --platform 'F:/College/verilog_digital_system/Vitis/continuous_platform' `
  --tools-bin 'F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin' `
  --record-root "$records"
```

输出必须在本 checkout `codex_out` 子目录，每次新建记录。入口只接受 `load`，不会执行旧 pre/post gate 或 Vitis Build。现有 `src/CMakeLists.txt` 仍按原绝对路径指向主 checkout gate；不能改成 review worktree 路径。新构建、更换实际工程或其他机器路径适配不在本合同内。

## 本批证据与交审

第二次真实运行退出 0，原生记录：`codex_out/entry-adaptation-smoke-02/20260924_114828_load_4ede0e949b/`。`request.json` 保存完整 argv/cwd/Python；三个工具调用分别保存 command、stdout、stderr、exit。结果为 `ARTIFACT_CHECK_PASS_NOT_BOARD`；GCC 13.3.0，object `0cb79780…`、ELF `4b7823bd…`、end `0x00a400c0`，启动入口属于唯一可执行且有文件数据的 PT_LOAD，完整历史及 launch 检查到达。

本写入批只交实现、依赖合同和真实只读 smoke。必要负例由下一串行验证批完成，之后交 B 复核准确提交；B 真正批准前不交 C 运行放行。C 仍负责采录。RTL/ARM 新编译、板测、时序、16 项服务上界、M1/H3 均 NOT RUN/UNVERIFIED；145 准备向量不是 RTL 通过。

行为/延迟/吞吐、时钟/复位/CDC/RDC、寄存器/IRQ/DMA 均无变化；无 Cycle Contract Delta。Vendor/target 沿用现存 2025.2 / Zynq 应用，未升级或生成 IP。Power NOT APPLICABLE。风险：本入口只检查当前盘上身份，无法证明板上真实加载、GUI Run 未绕过入口或未来文件未改变。
