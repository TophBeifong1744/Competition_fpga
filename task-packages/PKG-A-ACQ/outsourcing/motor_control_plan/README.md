# 声源跟随转台：成品采购方案与仿真交付

返工复核入口：先读 `rework_notes.md`，执行 `python check_delivery.py --root .`。当前门控示例为 **556项检查**；下文及 `report.html` 中15项是原始方案快照，旧结果保存为 `results/control_checks_original.json`。物理模型与历史数值结论保持不变。清单v2依据Git blob字节，不沿用旧清单的工作区换行哈希。

日期：2026-09-12。范围：成品选购条件、控制方案、离线动力学验证。用户确认载荷在几十克到 1 kg 内；不包含机械加工图、自制电路、采购下单或实际板上固件。

**建议采用带独立承重结构的成品单轴转台，配套步进电机、驱动器和输出位置反馈。现有仿真支持下述参数范围内的方案可行性，不能替代具体商品的性能证明。**

## 先看这些文件

- `motor_plan.md`：完整方案、选购条件、控制流程、结果和适用边界。
- `report.html`：可离线打开的结果概览和曲线。
- `results/verification.json`：数值验证汇总。
- `results/cases.csv`：149 个正常参数工况的逐项结果。
- `simulate.py`：实际运行的动力学模型与测试入口。
- `validate_control.py`：15 项独立的上层控制逻辑示例检查。
- `run_all.ps1`：复跑入口，默认写入新目录，保留本次结果。

## 核心结果

| 检查 | 实际结果 |
|---|---|
| 正常参数工况 | 149/149 最终误差 ≤1°，149/149 按时稳定 |
| 最差最终误差 | 0.564745°；指仿真最后 0.5 秒的最大绝对误差 |
| 90°动作最慢稳定时间 | 3.135 秒；动作规划为 3 秒 |
| 正反往返 | 轻载与重载两项通过 |
| 受控停止 | 独立重载用例通过 |
| 欠扭矩反例 | 按预期失败，最终误差约 89.93° |
| 数值步长核验 | 0.2 ms 减为 0.1 ms，三个代表工况最大角度差 0.010186° |
| 上层逻辑 | 15 项合成输入检查通过，不等于实际控制器已实现 |

## 如何复跑

实测环境：Windows，Python 3.13.5、NumPy 2.3.2、Matplotlib；本机 Python 为 `D:\Python\python.exe`。其他机器需要安装 Python、NumPy 和 Matplotlib。

在本文件所在目录运行：

```powershell
.\run_all.ps1 -PythonPath 'D:\Python\python.exe'
```

也可以分别运行：

```powershell
python simulate.py --out results-new
python validate_control.py --out results-new
```

预计输出：参数 JSON、逐项结果 CSV、完整时序 NPZ、四个代表工况 CSV、两张 PNG 曲线、验证 JSON 和运行日志。当前机器一次动力学复跑约 80 秒，实际时间依电脑而变。

`run_all.ps1` 还会检查正常用例、往返、受控停止、数值核验与预期失败反例；失败返回非零退出码。随机参数种子固定为 20260912。`report.html` 是本次结果的快照，复跑不会自动更新它。

## 数据读取

```python
import numpy as np
a = np.load('results/traces.npz')
t = a['t']                  # 秒，保存间隔 1 ms
q = a['state'][:, 2, :]      # 输出轴角度，弧度
w = a['state'][:, 3, :]      # 输出轴角速度，弧度/秒
```

`state` 的轴顺序为 时间×状态×工况，状态依次是电机角度折算到输出轴后的 x、x 的角速度、实际输出角 q、q 的角速度。正常时序的工况顺序对应 `parameters.json` 删除 `full_range` 后的顺序。全行程、往返、受控停止和欠扭矩反例单独保存。`cases.csv` 的全行程行在最后。

下一步：按报告向成品供应商核实动态扭矩、实际减速比、位置反馈和停止性能。商品结构或驱动控制方式不同，应替换模型参数再评估，不能直接继承本次通过结论。
