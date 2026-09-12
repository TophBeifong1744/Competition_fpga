# Motor plan scoped rework

基准：`e6932a815340b8276e291263c1acb965c15b1f7f`。分支：`codex/c-rtl-001-outsourcing-docs`。

## 故障优先级补修（基于34164d5）

本次仅修改 `validate_control.py` 的优先级及组合测试，并更新控制检查结果、日志、说明和清单。优先顺序为：已有锁存 → 任一独立有效的急停/限位/编码器超时/心跳超时 → 一般输入有效性 → 普通门控。有效急停和限位使用明确的布尔True；已确认超时必须是非布尔、有限实数且超过原阈值。非法年龄本身不被伪装为确定超时，仍按原无效输入策略处理。

这样，编码器超时与NaN方向同时出现，或有效急停与非法limit/moving同时出现，均进入BRAKE、清空候选并锁存，保持目标不变。合法故障不再被其他字段的NaN、非法标志、未来帧或时钟回退挡住。

在旧提交中实际复现上述两例返回DECEL，记录于新的 `results/control_run.log`。保留原380项，增加176项组合断言（4种故障×不冲突的非法字段×静止/运动，分别检查立即制动及输入恢复后的锁存），合计556项通过。真实运行时间和环境见该日志；未重跑物理仿真，也未增加硬件工作。

## 修改与原因

- 父目录 `* text eol=lf` 会转换 PNG/NPZ 字节。本目录 `.gitattributes` 仅对这两个扩展名关闭文本、diff 和 merge 处理；未修改上级规则。
- 从原始输出目录的完整原件恢复 2 PNG、5 NPZ 和 `results/run.log`。恢复前核对原件清单哈希并实际解码/读取。没有重新生成或伪造历史物理仿真；原日志只有环境、结果和耗时，没有历史墙钟起止时间。恢复时间、来源和源字节哈希见 `results/restoration.json`。文本日志以 LF 存储，二进制必须逐字节保持原样。
- `.gitignore` 仅例外允许 `results/run.log`、`results/control_run.log`、`results/rework_checks.log` 三个指定日志。旧15项控制检查保存在 `results/control_checks_original.json`；当前检查结果为556项。
- `manifest.json` 升级为 v2，哈希由已暂存的 **Git blob实际字节** 生成，且生成时强制工作区字节相同。清单覆盖全部交付文件，唯独不包含它自身。文本统一LF，杜绝按CRLF工作区字节算哈希、却交付LF仓库字节的问题。
- `check_delivery.py` 检查必要文件、清单覆盖、逐文件SHA-256、PNG格式/校验/完整解码，以及每个NPZ的ZIP CRC和每个数组实际读取（禁用pickle）。任何失败退出码为1。生成清单前也执行解码，不能用改哈希掩盖损坏。
- `test_delivery.py` 在临时副本测试：完好包、缺日志、哈希不匹配、匹配伪造哈希的坏PNG、匹配伪造哈希的截断NPZ、ZIP合法但数组损坏、恢复后的完好包。原件不受修改。
- `run_all.ps1` 对任何已存在的输出目录直接拒绝，连空目录也不覆盖。`validate_control.py` 也拒绝覆盖已存在的 `control_checks.json`。支持的整包复跑入口是 `run_all.ps1`；不要直接对历史 `results` 调用低层 `simulate.py`。

## 门控语义

`validate_control.py` 保留原15项检查，增加541项检查，总计556项。

- 候选组中的每帧都必须在当前时刻100 ms内；长断帧后旧票自动过期。新帧只算一票，重新凑足三个新帧才能启动。
- 帧时间戳严格递增。重复和倒序帧清空所有候选票，但不回退已见时间戳上界；恢复须提供三个更新且新鲜的帧。若数据源时钟重置，需要上层显式重新初始化，不能把倒序当正常恢复。
- `now` 回退同样拒绝；新鲜度端点100 ms允许极小浮点舍入容差1e-12秒。
- 对当前时间、角度、置信度、帧时间、位置、反馈年龄、心跳年龄逐项拒绝NaN、正负无穷、None、字符串及布尔冒充数字。时间/年龄不得为负，置信度须在[0,1]，未来帧也拒绝；控制标志必须是布尔值。
- 没有独立有效故障时，无效输入不更新目标、清空候选；静止进入HOLD，正在运动进入既有DECEL策略。已有锁存及本拍独立有效的超时、限位、急停均优先于一般无效输入，进入或保持BRAKE锁存。
- 等待新票时明确回到ACQUIRE；已作出的决策清空票数，不把上次的票借给下一次动作。运动中不重定向目标，范围外目标也按DECEL处理。

556项涵盖原正常流程、三条复核反例、100 ms整组窗口及边界、重复/倒序/长断帧后的三帧恢复、各数值字段的无效值在静止/运动两种状态下的拒绝与恢复，以及锁存等情况。实际UTC起止、Python与系统环境见新控制JSON及 `control_run.log`。

## 实际检查与复核命令

本地实际结果：556项门控检查通过；完整性检查读取2张PNG、5个NPZ内全部35个数组；7项完整性正/反例检查通过；2项已有证据覆盖拒绝检查均返回非零，且原证据哈希保持不变。执行环境为Windows 11、Python 3.13.5，真实执行时间及标准输出见本轮两个日志。物理仿真未重跑。

在本目录运行（Python需要NumPy与Pillow；重跑物理模型另需Matplotlib）：

```powershell
python check_delivery.py --root .
python test_delivery.py --root .
python validate_control.py --out results-reproduced-control-review
.\run_all.ps1 -PythonPath 'D:\Python\python.exe' -OutputDirectory results-reproduced-physics-review
```

输出目录必须是新的。前两条不修改交付证据；后两条是独立复跑。原物理源码及模型保持不变，149项及附加物理结果采用恢复的历史原件，不声称本轮再次运行了物理模型。

维护者生成清单的顺序：先将本目录全部改动暂存，再执行以下命令，然后暂存新清单并检查提交diff范围：

```powershell
python check_delivery.py --root . --write-manifest-from-index
python check_delivery.py --root .
```

`--write-manifest-from-index` 会读取本目录Git index中每个blob；工作区存在CRLF差异或未列入暂存的新交付文件会拒绝。不要以修改哈希代替恢复二进制。

## 远端复核

必须推送后按**准确远端提交SHA**取回目录再运行上述完整性检查。可在独立临时clone中fetch任务分支，确认抓到的SHA等于交付SHA，使用 `git archive --format=tar --output=motor_review.tar <SHA> task-packages/PKG-A-ACQ/outsourcing/motor_control_plan`，解压到新目录后执行 `check_delivery.py` 与 `test_delivery.py`。使用tar避免PowerShell文本管道修改二进制。

最终远端取回检查状态以交付回复附带的准确SHA及实际检查输出为准；本文件不会预先声称尚未执行的远端验证通过。由于提交无法包含自己的SHA，远端验证回执与最终回复关联，不为回填SHA改写已验证提交。

## 未验证边界

本轮只修复交付完整性和现有上层目标门控示例。未实现INIT/归零/SETTLE硬件控制器，未改主工程RTL/BD/XDC、采购、接板或分工。合成软件检查通过不代表实物转台或声学闭环验收通过。
