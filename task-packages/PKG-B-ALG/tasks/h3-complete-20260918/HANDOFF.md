# HANDOFF：A → B（四路 H3 9/18 候选）

## 固定版本与范围

- 仓库：`TophBeifong1744/Competition_fpga`。
- 基线：`5cfa02e51af44bb5c930babf732ddc864a1ab6cd`，已核实包含 `21780c3`。
- 分支：`task/member-a-0918-h3-closeout`。
- 待审提交：由工作执行推送后填写准确 SHA；不要按移动分支名批准。
- 新增范围：`task-packages/PKG-B-ALG/tasks/h3-complete-20260918/` 与 `deliverables/phase-2026-09-18/` 的 DRAFT。
- 未修改：默认 PHAT、Tracker、四路录音、RTL/BD/XDC/Vitis、Skill 活动源码、历史 run/manifest/失败记录。

## 相对主线新增内容

1. 四路输入/几何/符号/数制合同。
2. 可移植整数全链 golden 及逐级NPZ检查器；它不是 AMD FFT bit-exact 声明。
3. 冻结阈值的存在门候选和真实 center/quiet 诊断；结果暴露 quiet 全过门，不能准入正式存在判定。
4. 四路 4FFT+6IFFT、PHAT/lag/DOA/DAS/DMA 的周期公式、缓存和带宽账本。
5. 对两项已批准 Skill 的增量身份/范围检查；没有重复全量测试。
6. H3准入建议、NOT_RUN/BLOCKED清单和独立复核提示词。

## B 应执行

```powershell
git fetch origin
git worktree add --detach <新目录> <准确待审SHA>
Set-Location <新目录>
$py = '<含NumPy 2.3.5的Python 3.12>'
$pkg = 'task-packages/PKG-B-ALG/tasks/h3-complete-20260918'
& $py -B "$pkg/source/reproduce.py" --repo . --out '<任务包外的新目录>'
```

重点独立核查：

- `inputs.json` 的18项绑定是否与待审提交一致；待审S1输入 `8f708e4` 不得被本包暗中当已批准主线输入。
- 11个逐级数组是否全码一致；Q12 lag、缺pair/秩不足、HOLD到期、方向切换和断流是否按合同发生。
- 当前存在门为何接受全部 quiet 帧；不能把允许扇区造成fresh=0改写成“存在门拒绝背景”。
- 73900周期只来自两个历史OOC测试槽，不能写成混合位宽整链测量；91080B是保守清单，不是BRAM映射。
- 三路音频复跑是否保持同一原始输入、共同时间轴和共同增益；无参考时音频收益仍为NOT_RUN。
- 两项Skill活动目录自批准SHA无变化；SKL-001迁移新案例、SKL-002真实PYNQ均未执行。

## 建议结论

建议最多批准“9/18 四路 H3 软件候选/缺口包可复现并入库”，不要批准完整H3。存在门、真实指标、供应商全链位精确、集成实时/时序、板端输出仍须保持未准入。
