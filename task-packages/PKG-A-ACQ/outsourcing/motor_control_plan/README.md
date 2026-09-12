# 分体采购与自主适配：双轴三维主用、二维兼容方案 V2.1

**当前采购方向：不含电机/控制器的双轴机械机构，两台电机、两路驱动、传动与输出编码器分别选购；团队完成装配、部件匹配、输出位置闭环和双轴协调调试。前期二维只动Yaw，Pitch可靠保持0°；后期三维启用两轴。**

本轮仅本地修改，未提交、未推送。具体商品SKU未冻结，当前是分体采购规格、适配路线与选型预算；不能按“1 kg”“堵转扭矩”宣传直接认定适配。

## 当前文件入口

- `motor_plan.md`：当前双轴主方案，包含机构/电机/驱动分体适配、二维兼容、停止策略及比赛展示证据计划。
- `report.html`：当前方案的离线可读页面。
- `size_dual_axis.py`：新增解析选型预算脚本；不是双轴动力学仿真。
- `results/dual_axis_selection_budget.json`：本轮真实执行的27项Pitch与3项Yaw预算和反例。
- `single_axis_reference.md` / `single_axis_report.html`：原单轴方案归档，不能作为当前必买清单。
- `validate_control.py`：556项单目标门控/故障优先级检查；未实现双轴协调控制器。
- `check_delivery.py` / `test_delivery.py`：文件完整性及损坏反例检查。

## 新方案与历史证据

| 内容 | 状态 |
|---|---|
| 双轴硬件架构、二维兼容模式 | 已形成方案 |
| 新增输出端扭矩与停止距离预算 | 已运行，假设范围内通过；不等于商品性能认证 |
| 两轴连续输出扭矩筛选目标 | 各≥1 N·m，具体成品仍需核实 |
| 完整双轴动力学、联合运动、实物保持与制动 | 未验证 |
| 原149项物理工况、误差0.565°、90°约3.135秒 | 仅旧单轴基线；本轮未改模型、未重跑，也不承诺新双轴具有同样性能 |
| 556项门控及故障组合测试 | 原逻辑参考，不能视为三维双轴软件已实现 |

## 本地复核与复跑

Python检查器需要NumPy、Pillow；历史物理模型另需Matplotlib。新增预算脚本只用Python标准库。

```powershell
python check_delivery.py --root .
python test_delivery.py --root .
python size_dual_axis.py --out results-reproduced-dual-axis-review
python validate_control.py --out results-reproduced-control-review
```

所有复跑输出使用新目录，不覆盖历史证据。`run_all.ps1`仍是旧单轴物理模型与门控的复跑入口，不是三维验证入口；直接调用低层 `simulate.py` 时不得写入历史results目录。

本地清单按实际字节重新生成，文本为LF，PNG/NPZ保持原字节，并核对Git clean规则不会转换它们。本轮没有暂存、提交或远端校验；今后获准提交前仍应用 `check_delivery.py --write-manifest-from-index` 按暂存Git字节重建清单。

下一步按 `motor_plan.md` 的接口表联合核对机构尺寸、电机运行力矩、传动比、驱动电流及编码器安装。Yaw 4:1、Pitch 6:1仅为候选，未冻结SKU。团队依次完成单轴调试、回差辨识、输出反馈对比、Pitch重力保持、双轴协调及二维/三维演示；这些是待完成工作。
