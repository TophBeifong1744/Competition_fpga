# 9/23工程收口：路线、后级数制与条件预算稳定子包

实际执行日期2026-09-20。本子包可交工作执行检查发布；**作者自检，不是独立批准，不是完整H3/实时/实板通过**。原 `increment-20260923`（f879a54）的29个发布文件逐项核对未变；新材料只在本目录。

## 当前来源与状态

- 本地main及本轮直接远端main：`1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78`。远端实际输出在evidence/remote-heads.json；共享目录有其他未提交工作，未切换/重置。
- B集中回复：`f5a4cea7a7cf7dcccf09720cfff92131e6157752`；A软件受审增量：`f879a54cf40359209895af955bcef92accdf79ea`，本轮未找到其独立批准记录，不当已批准。
- BRAM来源：`e4f9eae3fe7e4104ff8a6827937e326954f90a82`，引用既有功能/OOC，不重跑。
- 新发现B算法候选：`bb964cbd5b4bee005702bebe6b9cee16d9b885d9`；其独立复核`5e343f2d9e9a372ad59bcc618571d4fb0002a7df`结论为**需修改、不合入**（R1浮点比较、R2原字节准备）。本包仅绑定未冻结的算法需求/状态类，不修改B复现器，不借本包测试关闭其返修。不假称有新的H3批准。

## 本轮真正新增

| 交付 | 结果/边界 |
|---|---|
| [ROUTE.md](ROUTE.md) | 推荐PS语义/分帧/所有权，PL数值服务；8包独立环+2帧工作区；身份、TTL、停止与晚错优先级；明确当前C与恢复语义的差异、待裁决项 |
| [NUMERIC.md](NUMERIC.md) | Hann、互谱/PHAT、逆变换结构/异常、lag、DOA、DAS独立数学对照；原Q30与AMD24分开；新gate状态边界 |
| [BUDGET.md](BUDGET.md) | 8FFT+6IFFT工作量、条件调度/缓存生命周期；非全null，也不伪装实测WCET |
| source/engineering_model.py | 独立所有权/身份/TTL/队列模型、IFFT守卫、参数化预算及内存容量检查；不是驱动或RTL |
| source/run_checks.py | 精确Git来源快照、独立Fraction/Decimal预期、可执行正负例、原受审包保护检查 |
| evidence/run03 | 最终21项检查PASS，退出0；原始逐项日志、反例、命令、环境、绑定及结果齐全 |

核心结果：1024个Hann系数、4096窗乘积、4097互谱向量、2054 PHAT归一化向量（对理想单位向量最大1码差，不宣称逐码全等）；新执行3个解析IFFT基向量及1个overflow反例。软件复现非法复数端点缺少守卫并提供独立修补建议。队列满、无界停顿、TTL/身份溢出、配置错配、共享RAM冲突和内存越界均有拒绝检查。

最终预算算术：保守串行 **1,633,192周期/hop**，超过1,066,666限额；较快乘法服务和外部等待W=50,000的试算 **477,432周期/hop**。后者全部为待验证假设，不是RTL/ARM测量。候选逻辑内存 **202,816B**，尚未赋实际地址/验证链接布局；不含所有IP内部RAM。**两例的生产结论均为REALTIME_BLOCKED**。

## 一条复跑入口

在仓库根执行；需要Python+NumPy、上述准确Git对象。输出目录必须不存在。没有Vivado/板卡依赖，不联网替换版本。

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$task = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923'
& $py -B "$task/source/run_checks.py" --out "$task/evidence/review-new"
```

本轮实际还加了 `--inspect-ps 'F:/College/verilog_digital_system/Vitis/four_mic_endurance/src/continuous'`，只读保存5个实际源码；不把它们当“板上正在运行”的证明。原始命令argv、工具环境、源码SHA与退出码分别在run03/command.json、bindings.json、results.json。历史run01/02保留，测试数量不累计。

生成/验证包清单：`python -B <本目录>/source/seal.py` 首次生成（存在则拒绝）；`python -B <本目录>/source/seal.py --verify` 复核。PACKAGE-SHA256.json覆盖本包所有文件（自身与其摘要除外），MANIFEST.sha256给清单哈希。

## 仍未完成/停止点

没有修改one、RTL/BD/XDC/IP、实际Vitis源码/配置，没有构建下载；本轮AMD/XSim、布局布线、CDC和实板均NOT_RUN。未重跑八段/run05/S1/计时/旧FFT/耐久，未补录、未改变reference25，未抢写B/C/Skill。

生产仍缺PS C语义桥及WCET、真实内存绑定、算法通路/MM2S选择、实际采样时钟锚/有限服务界、精确IP配置和后级AMD逐码对照、A/B生产数制/ABI确认。新gate全流整数化未在本轮执行。不是仅把这些缺项重列：已经交付可执行路线/算术/异常/调度模型供下一阶段逐项替换假设。

到此停止，由工作执行检查本稳定子包、发布准确待审SHA，再交B独立复核。本任务未提交、推送、合入或自行验收。
