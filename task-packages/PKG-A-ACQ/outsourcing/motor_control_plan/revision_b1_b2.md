# B1/B2限定修订交付

基准：f90d608fdb4aaaa9cfb0c528732f7e0b94530e3c；复核发布：d56ccedc6ef6b99ddf3a6764a08b5e0d7ee6c2f8。开始时fetch成功，本地HEAD与远端作者分支均为f90d608，工作区及暂存区为空。已读取origin/main协作约定、team-workflow、current-status、project-plan及motor-f90d608复核记录。没有切换或合并main，没有新增采购、装配、控制开发或交期。

B1：只检查最大惯量漏掉延迟中的1/J重力加速项。保留原结果和10.983615°反例，改为检查惯量两端并说明凸性、单调性，覆盖连续条件包络；列出48组Pitch、3组Yaw停止检查和原27组历史停止复算（1组失败）。Pitch收窄为J∈[0.004,0.012]，Yaw为[0.01,0.04] kg·m²；其余边界不变，最坏9.488788°和8.612838°。不支持区间外设备，也不要求加配重或新增硬件任务。

B2：motor_plan第11节明确独立失电施加的动态制动及静态保持要求，补齐上电/复位/回零/停车/保持/失联/驱动故障/急停/掉电/恢复动作表。先建立电机承载才释放制动，先确认制动承载才降流或禁用；故障和恢复禁止自动释放/重启。正常减速、停脉冲、断驱动、机械保持与动态制动分别说明。表格为设计原则，不是已实现互锁。

实际运行：results/revision_b1_b2/commands.json含真实UTC、Python、平台、命令、输出和退出码；sizing/selection_budget.json包含所有新旧预算。5个预算回归测试含独立展开式、连续区间2002点核对、三组分段积分、非法数值及弱制动原因校验；原门控回归556项通过，仅作为原逻辑未回退证据。预算拒绝覆盖检查明确匹配FileExistsError，且验证原输出哈希不变，环境错误不能算预期反例。

交付完整性及7项损坏反例输出见delivery_commands.json。最终清单由暂存Git blob重建，再从准确远端提交提取重验；远端SHA和发布后检查回执由交付消息报告，避免在提交内容内自引用本次SHA。旧results和single_axis归档保持字节，未重跑149项物理模型。

## 复现

在本任务包目录运行，Python 3（本轮3.13.5）；预算和回归仅标准库，完整性/损坏反例需要NumPy、Pillow。validate_control为标准库。所有输出必须使用不存在的新目录。

```powershell
python -B size_dual_axis.py --out results-reproduced-b1-review
python -B test_stop_budget.py
python -B validate_control.py --out results-reproduced-b1-control
python -B check_delivery.py --root .
python -B test_delivery.py --root .
```

## 申请范围和未验证项

申请对B1停止包络及B2安全原则独立复核，活动位置保持现有motor_control_plan任务包；不申请RTL/系统接入或实物批准。具体SKU、惯量/外力/储能/延迟实测、制动静态/动态能力、完整双轴动力学、控制器实现、掉电试验和声学闭环仍未验证。旧149项及556项不可迁移为双轴性能证明。作者分支仍有任务，保留且不自行合main，不删除唯一证据或独立复核记录。
