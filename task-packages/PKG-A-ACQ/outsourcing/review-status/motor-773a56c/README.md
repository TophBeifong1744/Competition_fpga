# C 转台研究包独立复核与发布

复核日期：2026-09-12。结论：**限定研究交付通过**，不代表转台实物、生产控制器或整机验收。

- 作者来源：`codex/c-rtl-001-outsourcing-docs`，准确批准 SHA `773a56cfacab51c9bb7c7e9f9a05c850c7c3e48b`。
- 上轮待修 SHA：`34164d557314bd25b65be6c4a35e70241f62e81f`。本轮仅 8 个包内文件变化，无越界改动。
- 唯一成果：[motor_control_plan](../../motor_control_plan/README.md)，33 个文件按作者 Git blob 原样导入，不在其目录添加复核文件或重算清单。
- 主线导入基线：`e670eef5de66e85981db8880bee6d41d9afb3a18`。仅导入本包和必要状态/复核记录，不整条合并 C 分支。

## 实际独立检查

环境：本机 Windows、Python 3.14.6、NumPy 2.4.6；图片由 Pillow 完整解码。输出使用新目录，不覆盖作者证据。

| 检查 | 结果与证据 |
| --- | --- |
| Git 交付完整性 | 32 项清单及哈希、2 PNG、5 NPZ 的 35 个数组通过；[delivery.json](delivery.json) |
| 作者控制回归独立执行 | 556/556，通过原 380 项及新增故障/非法输入组合；[control_checks.json](control_checks.json) |
| 独立优先级与恢复检查 | 36/36；同一脚本在旧 34164d5 上复现 10 个失败断言，在新版全部通过；[priority.json](priority.json)、[检查源文件](review_priority.py) |
| 交付检查器正反例 | 7/7；覆盖缺件、哈希不符、假匹配哈希的坏图片/坏压缩包/坏数组及恢复后的完好包 |

本次修复使已确认的急停、限位、编码器超时和心跳超时优先于普通非法输入，进入 BRAKE、清空候选并锁存；非法年龄本身不伪装成已确认超时。没有已确认故障时保持原 HOLD/DECEL 处理，三新帧恢复和旧票过期不变。未发现本轮阻断问题。

## 批准与未批准范围

批准：成品转台选购条件说明、离线动力学模型和原始结果、上层控制示例及交付工具，供后续报告和方案研究引用。软件检查不是商品性能证明；采购与实物验证未批准。

本轮物理模型未变，未重新运行物理仿真；作者原物理结果按研究证据身份保留。没有修改或验证 RTL、BD、XDC、PS、综合、实现、时序或板上运行。没有将示例移入生产 `rtl/`、`ps/`：原因是仅批准研究用途，尚无实际执行器接口或系统接入证据；后续若启动转台工程，由 A 再明确接口与验证范围，不现在向 C 派开放研究。

本次不是阶段验收，不关闭 9/16 阶段或 H1/H2/H3，不倒填旧阶段快照。C004-R2 暂缓、005 不启动、四麦 V1 与 A/B/C 正式职责均不变。

## 复现

从仓库根目录，在新的外部输出目录执行；需要 Python、NumPy、Pillow：

```powershell
$pkg = 'task-packages/PKG-A-ACQ/outsourcing/motor_control_plan'
$review = 'task-packages/PKG-A-ACQ/outsourcing/review-status/motor-773a56c'
python -B "$pkg/check_delivery.py" --root $pkg
python -B "$pkg/test_delivery.py" --root $pkg
python -B "$pkg/validate_control.py" --out '<新的外部输出目录>/control'
python -B "$review/review_priority.py" --package $pkg --repo . --output '<新的外部输出目录>/priority.json'
```

独立脚本通过 Git 读取固定旧版并核实新版源码身份，需要本地保有上述准确提交。它只读被测源码，且拒绝覆盖已有复核输出。物理模型需要 Matplotlib；本轮无需重跑。

## 发布与本地收尾

发布前：共享 main 与 origin/main 均为上述导入基线，本包无已有修改、未跟踪或忽略材料；另有 9 项 PYNQ Skill 修改/新增，与本批无关，保留且不夹带。独立发布工作树承载本批，避免切换或重置共享脏目录。

发布提交及最终本地/远端一致性由本记录后续收尾补充并向用户报告。C 原分支仍含未关闭内容，不能删除；只清理本轮已经结束的临时发布分支和核实可恢复的重复副本，不删除此前唯一复核证据。
