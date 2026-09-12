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

成果已由 `d57ae4719d80e1e15a1437b485c354d6faa0abd9` 正常推送 main。2026-09-12 18:48（UTC+8）核对实际共享目录：本地 main、origin/main、直接查询远端 main 三者均为该 SHA，领先/落后 `0/0`；包内容与批准 SHA 完全相同。本收尾记录另行提交，不回写作者文件。

| 回报项 | 实际处理 |
| --- | --- |
| 发布后验证 | 导入位置重跑 556 项控制及 36 项独立检查通过，见 [post-import-control.json](post-import-control.json)、[post-import-priority.json](post-import-priority.json)；共享 main 再次完整性检查通过 |
| 本批本地材料 | 修改/暂存、未跟踪与忽略项均检查，本批无未说明遗漏；独立脚本和两处运行结果均入库，JSON 通过局部属性保留原字节 |
| 其他在做任务 | 共享目录仍有 9 项 PYNQ Skill 修改/新增；快进前后逐文件哈希相同，未夹带、删除或隐藏 |
| 唯一材料入口 | 作者完整包 `../../motor_control_plan/`；本目录只存独立复核脚本、结果与发布说明，不复制另一套作者源码 |
| 待审分支 | `codex/c-rtl-001-outsourcing-docs` 保留：C004 等差异及正式批准未关闭，不因本研究包通过整条合并/删除 |
| 清理范围 | 仅本轮 `motor-publish-773a56c` 临时工作树、`codex/review-motor-773a56c` 临时本地分支及 `motor-review-773a56c` 重复提取/运行目录；删除前逐文件对照已发布内容，作者包与复核结果由 main 恢复，源提交亦保留在 C 分支 |
| 保留历史 | 上轮 `motor-review-34164d5` 的失败复核和首轮 `motor-review-e6932a8` 的独立动力学结果不是本轮重复缓存，不删除；不动其他成员工作树 |
| B/C 电脑 | 本次无法访问，未代签本地同步；由成员按统一流程自行核对 |

以上同步核查完成；本收尾补充推送后再核对三方 SHA 并向用户报告最终提交号，临时目录清理结果以最终回报为准。
