# 复现输入与原执行命令

工具/器件：Vivado/XSim 2025.2 SW6299465，`xc7z020clg400-1`。此说明提供相同输入与命令；没有因发布再运行EDA。先将Vivado2025.2的原生命令环境配置到当前命令行，不改变全局环境。原runner记录了当时直接调用native exe所需的进程环境；其中机器绝对路径是历史事实。

## 限定仿真

在本仓库根目录的Vivado2025.2 Command Prompt中，为每个case分别建立**新的空**`codex_out`子目录。下面是`evidence` case的原生命令，输入都来自发布的准确文件；不是执行历史路径已绑定的原runner。

```bat
set "REPO=%CD%"
set "PACK=%REPO%\docs\evidence\issue17-c-evidence-lut-fix-20261011"
set "OUT=%REPO%\codex_out\i17-evidence-replay-evidence"
mkdir "%OUT%"
cd /d "%OUT%"
xvlog --sv "%REPO%\project\rtl\c_board\i17_vio_evidence.sv" "%PACK%\originals\selftest\i17_vio_evidence_before.sv" "%PACK%\originals\selftest\tb_evidence.sv"
xelab work.tb_evidence --snapshot test --debug off
xsim test --runall --onerror quit --onfinish quit --sv_seed 17010
```

每步先检查实际退出状态，再执行下一步；另存原生log和命令输出。正确结束须包含`PUBLIC_READ_COMPLETE reads=6656 miter_cycles=7772`及`EVIDENCE_COMPLETE checks=29178 pending=0`，且没有Fatal。需要观察波形时，完成xelab后可用XSim GUI打开该snapshot；GUI观察不代替上述检查器完成标记。

`words` case使用另一个新空目录，将最终输入TB换成`selftest/tb_words.sv`、展开顶层换成`work.tb_words`，其余相同；期望`WORD_ORACLE_COMPLETE checks=409600 ... pending=0`且无Fatal。

`canary` case使用新的空目录、同一`tb_evidence.sv`，xsim命令增加`--testplusarg CANARY_DATA`。预期在787ns、kind3/word17首次出现`Fatal: DATA_CHECK`（expected90060060 / got90060160），且不能出现成功完成标记。XSim在fatal时仍可能返回0；只看退出码不构成负例有效证据。原runner较弱的匹配条件已记录为LOW `C-EVID-LUT-SH-001`，本发布没有修改它。

## 同条件单模块综合

在仓库内新的空目录`codex_out/<新的诊断目录>/`只复制以下原件，保持相对层次：

- `originals/diagnostic_synth.tcl`
- `originals/diagnostic_clock.xdc`
- `originals/inputs/i17_vio_evidence_before.sv` → `inputs/i17_vio_evidence_before.sv`

此位置使Tcl中的`../../project/rtl/c_board/i17_vio_evidence.sv`正确指向活动候选。不要复制已有`synth_before/after`输出进去；脚本会拒绝覆盖已有目录。然后使用该Tcl文件的**绝对路径**执行原命令：

```bat
vivado -mode batch -source "<新目录绝对路径>/diagnostic_synth.tcl" -log "<新目录绝对路径>/diagnostic_synth.log" -journal "<新目录绝对路径>/diagnostic_synth.jou"
```

输出为`synth_before/after`下的`utilization.rpt`、`hierarchy.rpt`和`primitive-counts.tsv`；两次均须显示`synth_design completed successfully`并最终退出0。共同诊断时钟16.276041667ns由Vivado按1ps精度取为16.276ns。该脚本只做两个独立模块的OOC综合，不打开原XPR或执行opt/place/route；结果仍不证明整机放得下或时序收敛。

原执行遇到受限环境的路径归一化错误后，曾以已授权诊断权限重试成功。若另一台机器遇到路径、license或工具环境错误，应先解决环境并保存失败原件，不改变产品RTL来绕过。
