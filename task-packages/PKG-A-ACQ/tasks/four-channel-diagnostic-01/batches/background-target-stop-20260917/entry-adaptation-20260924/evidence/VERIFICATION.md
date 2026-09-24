# #13 S1 组合入口验证记录

2026-09-24。检查器回归 **47/47 命中预期（5 个正例、42 个拒绝负例）**，其中无需 A 机工具或实际工程的离线入口为 **46/46**。这是 `PREFLIGHT` 检查器证据，结论 `CHECKER_CASES_MATCHED_PENDING_REVIEW`，待 B 对准确提交独立复核；不是 RTL 仿真、真实下载、板测或阶段验收。

## 固定输入与独立预期

- 实现检查点 `7e9352a94f59c442f715997e8d95785913eac301`；`check_load.py` SHA256 `9407acdf3cd4e9f14a1779bb0b3d2baf9714c60e413b35f4eb6299cfc71217c1`。
- 原问题依据准确 `7274df873d6a36da8e16ca54f05688d3c7f09689` 中 `algorithm-interface-review-20260918/evidence/scene-dependency-20260921-02/`；旧 S1 policy 的 checker `f9572f…` 与批准 `21c141b223936730c2ce5139624fcedb412adafb` 的 `d2f5de…` 有启动/命令安全语义差异。
- S1 合同来自未修改的 `background-target-stop-20260917/POLICY.json`、原方案及归档：6000000 us、288000 目标组、300000 容量组、9600000 B、两端各 64 B guard；程序区不得进入 RX `[0x01000000,0x01100000)`，计时除数为 333333343。
- 启动参考为 `8f708e42caf32c1de6f30726298e3edf0e1970b6` 与 `7274df8` 已有 `delivery-01/versions/build/four_mic_endurance.elf`，SHA256 `4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6`。测试不根据本次待检输出生成期望。
- 离线对象夹具是 Git 内 `command-order-fix-01/before-fix/app/build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj`，SHA256 `3fd07ea3b80a955c660291e4a38fbee2ca022bb10088f725dedea487ba4bc150`，由该目录 `SHA256.json` 独立绑定。它与上述 ELF 仅组成 checker fixture，**不声称同次构建**。真实完整 load 使用的对象为 `0cb797800bb2f9791d35fa4c81bd995db6696513b0540d959c2e5e2614cabdc2`，见原始 live 结果。

## Requirement → Test 追溯

| ID / 独立要求 | 测试与原始观察 | 证据边界 |
| --- | --- | --- |
| R1：保持 S1 时长、容量、guard、DDR/RX 和计时语义 | `archived_s1_composed_compiled` 正例；对象/ELF 旧除数、10 秒合同、容量、archive size、RX 越界均命中对应错误 | 真实归档 ELF/object；未执行 ARM 程序 |
| R2：导入前绑定完整新依赖及独立启动参考 | dependency 正例；`command_contract` 和 S1 启动 ELF 的 missing/replaced/omitted_pin 共 6 负例；拒绝前后已导入模块身份不变 | 仅把测试安装根映射到当前 checkout；生产 policy 不变。定点移除的缺失文件是故障注入，不把其他环境缺失计作检出 |
| R3：四条命令、参数边界和大小写保持，只有两个独立前置命令允许交换 | 原序/允许交换正例；缺失/额外/重复/编链交换、宏/编译选项/辅助 gate 改动；`-e`、`--defsym`、`--wrap`、`-L,/../lscript.ld` 在组合入口及批准 parser 均拒绝 | 无编译/链接子进程；使用冻结命令文本 |
| R4：入口为固定 ARM vector、唯一可执行且 file-backed PT_LOAD，vector/_boot/startup bytes 不变 | RX entry、Thumb entry、零 filesz、取消 executable、vector/_boot 符号、vector/reset bytes 共 8 负例 | 每个 ELF 突变经过组合 `compiled()`；预期错误必须精确命中 |
| R5：加载身份及路径正确 | 归档 launch 正例、错误 ELF/bit 路径、错误 bit/XSA 字节；A 环境额外错误 platform 路径 | 路径测试使用明确的微型占位文件，仅证明路径检查；bit/XSA 是身份边界单测。完整 .o/ELF/map/platform/BSP/launch 链复用 live-load-02 |
| R6：检查期间输入替换须拒绝 | `input_changed_after_check` | 独立小文件 before/after，不修改真实输入 |

每个用例在 `result.json` 记录要求、预期 accept/reject、错误文本、实际异常和作用范围。拒绝类型/原因不匹配即失败；未预期 OS/路径错误归 `TOOL_ENV_FAIL`，不会算检出。所有突变及依赖夹具只留在 `codex_out`，未复制进本交审包。

## 按目标区分的结果

| 目标 | 结果 / 原始入口 |
| --- | --- |
| B Windows/Python 3.11+，无 A 机 F 盘 | [offline-checks/result.json](offline-checks/result.json)：46/46，退出 0；原始命令、Python、stdout/stderr 同目录 |
| A 机同一脚本加 `--live` | [checks-with-live-path/result.json](checks-with-live-path/result.json)：47/47，退出 0；仅增加错误平台路径的早拒绝。与离线 46 项重叠，不能累加成 93 项 |
| 实际完整 load 正例 | **复用，未重跑** [live-load-02/result.json](live-load-02/result.json)：`ARTIFACT_CHECK_PASS_NOT_BOARD`；精确 argv/cwd、3 个只读工具 command/log/exit、全部输入哈希齐全 |
| 首次组合失败 | 原字节保留 [live-first-rejected/failure.json](live-first-rejected/failure.json)：`Startup vector/reset bytes changed`。这是另一应用 ELF 作为参考导致的错误参考选择，分类 `REFERENCE_MODEL_FAIL`；不是 DUT 缺陷 |
| 启动参考差异诊断 | [startup-reference/comparison.json](startup-reference/comparison.json)：208 B 中 9 word 差异；两份原始 objdump command/stdout/stderr/exit 可供 B 独立核对。初版 checker SHA 仅由实现作者 README 记录，首错原始 request 自身未记录源码哈希 |
| 新构建 / RTL 仿真 / 下载 / 板测 / STA / CDC | `NOT_RUN`；16 服务上界及生产实时结论 `UNVERIFIED` |

最初本地 47 项运行保留在 `codex_out/s1-verification-01`；之后仅收紧故意缺文件负例的文件名匹配并移除未用变量，以最终脚本分别执行离线及 A 机目标。没有产品改动或测试放宽，没有未解决的产品 finding。

## B 离线复跑

在本候选 checkout 根，使用 Windows 原生 Python 3.11+。输出目录必须尚不存在；测试不调用 GCC、Ninja、objdump、Vivado/Vitis 或板卡。

```powershell
$entry = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/entry-adaptation-20260924'
python -B "$entry/tests/run_checks.py" --out "$(Get-Location)/codex_out/s1-b-review-new"
```

该离线模式把 unit fixture 的 `installed_task_root` 映射到当前 checkout，因此不证明 B 机器上的实际安装/加载链。批准的 argv parser 使用 Windows API，非 Windows 运行应报告环境失败。`--live` 的第 47 项仅在持有生产 policy 所列 A 机路径时运行；实际完整 load 的复跑命令仍见父目录 README。

## 封存与交审

本批只新增 `tests/run_checks.py`、本验证记录及 `evidence` 原字节副本。产品 `check_load.py`、`DEPENDENCIES.json`、所有冻结源/旧清单、实际工程均未修改。每份复制来源和字节哈希见 [SOURCE-INDEX.json](SOURCE-INDEX.json)；本批文件哈希见 `VERIFICATION-SHA256.json`。首次失败和所有原始诊断保留原位。

需要 B 在主会话发布的准确最终 SHA 上独立审查需求、参考来源、各拒绝原因、组合 live 证据与批准范围。验证资产作者未自签自己的验收证据，也不代 B 批准。C 仍负责采录；145 准备向量不是 RTL 通过。
