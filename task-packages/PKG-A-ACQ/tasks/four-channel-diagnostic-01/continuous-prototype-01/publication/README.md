# 四路连续采集原型：本次待审入口

2026-09-15。工作执行已核对交付完整性，申请 B 独立限定复核；尚未批准或接入正式主线工程。发布基线为 `058aa3095fd4df7392645004b164adb4eec52041`，待审分支为 `codex/toph/continuous-prototype-20260915`。

## 先选对版本

| 用途 | 唯一正确入口 | 边界 |
| --- | --- | --- |
| 本次计时修正后实板证据 | [board-run-20260915-02/README.md](../board-run-20260915-02/README.md)，其 ps/、runtime/、configuration/、build/ | 当前修复版，ELF见下；两段分别报告 |
| 首次问题与修复前原件 | [board-run-20260915-01](../board-run-20260915-01/README.md) | 计时约缩小四倍，旧时间不可作真实微秒 |
| 不变的连续核心、RTL、TB | [ps/continuous_core.c](../ps/continuous_core.c)、[rtl](../rtl/)、[sim](../sim/)、[tests](../tests/) | 核心与新快照核对一致；未在本轮重跑 RTL 仿真 |
| 最早候选构建/运行史 | 根 README/RESULTS/REPRODUCE、ps/main_continuous.c、run.py、load_candidate.tcl、delivery-01/release | **历史未修计时版本，不是本次修复固件的重建/加载入口**；原记录和白名单不改写 |
| 本轮只读检查和测试复跑 | 本目录 checks/、verify_package.py | 工作执行交付检查，不代替 B 独立复核 |

根 README 中“实板未执行”和“下一步上板”属于早先封存阶段文字；当前状态以此页及 board-run-20260915-02 为准。其原字节被历史清单覆盖，故保留，不将新结论回写旧证据。新发布总清单为本目录 SHA256.json，原 PACKAGE-SHA256.json 仅覆盖最早165项，不能误认为涵盖后来两轮实板文件。

当前实际修复版：
- ELF SHA-256：`ebc576e2bfe87ca45c06fb62359babc36f8d474505a97ff6d121336d2a3c3fa3`。
- bit SHA-256：`b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf`；当前 XSA 内嵌相同 bit。
- 旧 release 的 bit 为44bf76e1…、ELF为445f7c7…、XSA不嵌bit，**不是本次用户原 one 构建的产物**。只能在明确历史标签下引用其构建证据，不能把两个硬件构建的哈希混用。
- 实际 Vitis 应用为 `F:/College/verilog_digital_system/Vitis/four_mic_continuous`，Run 配置 four_mic_continuous_app_hw_1。修复版归档提供原源码、对象/ELF及配置快照；没有把历史 run.py 白名单更新为已验证的新固件构建器。

如需重新构建/加载，先按用户操作约定确认实际工程选择，使用修复版 ps/runtime 对应配置；本轮不运行旧 build/load 脚本，也不要求 B 额外上板。真实修复版的一键安全重建入口更新须另行实现/验证，不能由本次归档批准自动覆盖。

## 本轮交付检查

1. 保留作者原200个文件：最早清单165项及自身、首轮9个文件、修正复测25个文件。修正复测 SHA256SUMS.txt 共24项，MANIFEST.json其中20项为外部原件；首轮清单只列7项，README及清单自身由新发布总清单补覆盖，旧清单不变。
2. 19份历史构建/失败ZIP均通过既有SHA-256与CRC检查，保留失败历史；未将仓库外散落的 continuous-work*/export 工作目录再整体提交。
3. 隔离发布位置运行修复版 check_evidence.py 通过；两段分别480250组/1921包/15368000字节，计时除数333333343；实际对象与ELF的64字节合同一致、全部加载范围不与RX交叠、XSA内bit匹配。
4. 在同一隔离位置重新运行候选入口10项及原34项安全测试、原C核心主机16个场景。**主机时间/IO/cache均为模拟回调，不验证实际 now_us BSP宏、硬件缓存或实板故障恢复。**
5. 只读核对当前磁盘20项实板配套原件和9项构建MD5一致；实际 one 的两份活动连续RTL与候选文本一致，BD中GPIO直接驱动four_mic_top_0/start。见 checks/live-input-check.json。这是磁盘状态，不是FPGA读回；未改 one 或 Vitis。
6. 本轮没有新 RTL/XSim、Vivado综合实现、Vitis固件构建、硬件下载或采录。历史 RTL/实现证据和用户本次实板操作分别保留，不把上述软件复跑扩大为新实板验证。

## B 的复现入口

先固定用户提供的准确提交SHA，在独立工作区保留原件。以下PowerShell在仓库根执行；Python需可用标准库，测试器无额外算法依赖：

```powershell
$ContinuousTask = Join-Path (Get-Location) 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01'
python -B "$ContinuousTask/publication/verify_package.py"
python -B "$ContinuousTask/board-run-20260915-02/check_evidence.py"
```

第二条原作者脚本固定使用 `F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin/arm-none-eabi-objdump.exe`。若B安装位置不同，**不要改冻结原件以消除哈希差异**：在额外独立副本适配这一个工具路径并记录差异，或使用本机可用ARM objdump独立核对now_us；缺少工具时该子项记环境未验证，不算通过。脚本复用邻级current_build/ps_contract.py，依赖已核对，不要求访问A的F盘工程。

可直接复跑无硬件单测：
```powershell
python -B -m unittest discover -s "$ContinuousTask/tests" -p test_entry.py -v
python -B -m unittest discover -s "$ContinuousTask/../current_build" -p test_build_current.py -v
```

主机16场景用根 run.py 的 **host子命令**，只编译未改变的continuous_core和测试，不使用旧main_continuous.c：
```powershell
python -B "$ContinuousTask/run.py" host --host-gcc '<本机原生gcc绝对路径>' --output '<已存在父目录下的全新绝对输出路径>'
```

不要将host/sim/check/完整build混为同一入口。新输出在包外，拒绝覆盖旧目录；实际参数、退出码和日志见 checks/safety/ 与 checks/host/。B复核记录也放在封存包外，避免改变总清单的文件集合。

## 批准申请与后续限制

仅申请连续采集原型源码、测试与两次实板记录入库，以及修复后两段停止排空/一次无复位重启的限定结论。**未保存完整10秒BIN，逐组正确性依赖PS在线检查，B不能凭汇总日志独立复算全部960500组。** 两段间漏存54638个ID为主动停止间隔，不拼接成20秒连续录音；累计字节不等于DDR同时占用。

修复影响所有基于now_us的时限/性能量；无实板故意超时/溢出注入，不能从主机模拟负例批准真实故障恢复。无独立墙钟/采样率校准，不宣称精密同步、正式M1/H3或一小时长稳。数值一致与文件字节一致分别记录。旧结果不自动覆盖新变更，默认算法及其他成员内容不在本次范围内。

B发现阻断先反馈，不边改作者实现边自审合并。限定通过后按准确范围合入、回归、推送和batch-closeout；实际生产入口更新、硬件/源码接入需要明确批准，不能直接调用历史计时错误固件。尚未批准前不清理本分支、发布工作树或唯一原件。
