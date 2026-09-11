# 四路接收诊断入口

当前状态（2026-09-11）：诊断入口已经 A 限定复核并经 PR #9 合入 main `e811c39`；已有四路杜邦线实录且 B 完成本轮可接收回执。见[真实输入登记与交接](real-input-20260911/README.md)。新增登记材料仍待 A 复核，不宣称完整 H2 完成。下文 run01 及原实现交付描述保留历史语境；A原接收清单A-REVIEW-INTAKE.md保持不变。

## 使用

在仓库根目录，Python3.12和NumPy：

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/diagnose.py 'F:/recordings/capture_01' --out 'F:/NUEC/diagnostic-capture-01'
```

输入目录必须有metadata.json和samples.csv，格式为H1 ss-data-draft-0.3。输出必须是新的目录且位于所有输入目录之外。先用仓库已有固定码型演示：

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/diagnose.py task-packages/PKG-B-ALG/reference/h1-ss-data-draft-0.3/payload/examples/h1/code-pattern task-packages/PKG-B-ALG/reference/h1-ss-data-draft-0.3/payload/examples/h1/restart --out F:/NUEC/four-channel-demo-new
```

多个目录按接收顺序传入同一次调用，共用ReaderSession检查配置/几何版本及同acquisition编号冲突；不同采集分开报告，不拼接。各单独进程不能发现彼此的配置冲突。

## 输出

- receipt.md：简短回执，包含能否解析、通道数、样本数、编号、配置、每路幅值和下一步建议。
- summary.json：完整统计、连续区间、缺号、各类错误标志行数、相关性、输入SHA和代码/环境信息。
- errors.json：错误行的原始PCM、编号、flags和CSV物理行号，或每个拒绝目录的首个格式错误。

退出码0表示所有目录可解析，仍可能有错误行和通道提示；不表示数据无异常。退出码2表示至少一份拒绝，或输出路径/运行参数错误。坏目录不会阻止其他目录的检查，失败记录也不会污染读取器配置注册表。

## 诊断规则与边界

1. 保留原uint64编号；JSON中编号和缺号计数输出为十进制字符串，避免浏览器转换double损失精度。不重编号、补样、排序、过滤、改增益。错误行完整保留。
2. 每路分别统计全部行与格式无错误行的范围、均值、RMS、去均值后的AC RMS、峰值和满量程端点数。满量程端点只提示检查削顶，不是已确定削顶次数；AC RMS仅统计，不生成高通/处理后音频。
3. 恒定通道、连续区间内完全相同/反相、绝对Pearson相关度≥0.995均给提示。默认至少32个连续无错样本才评估；这些是可调整诊断启发式，不是验收门限，不据此认定复制、同步、物理映射或相位正确。不会跨错误行/缺号拼接相关计算。短码型通常样本不足，会明确未评估。
4. relock按标志行计数，不当重启事件计数；新acquisition是来源声明，重启是否实际发生未验证。缺号仅报告可观察的编号差；文件间未知间隔不虚构缺失数。
5. 复用严格读取器的首错拒绝规则：格式非法时没有部分波形统计，不跳过坏行“修好”录音；只报告该文件首个错误，不能称已列全所有坏行。已可解析记录中的标志错误行则全部列出。
6. 单麦ss-mono-diagnostic-0.2、三列/六列、未支持schema会拒绝，不适配成四路。来源及accepted/calibrated字段只转述；报告始终保留未核验，不输出DOA/SNR、不批准H2。
7. 继承原读取器整段读入内存，适用于首批短片段；未验证小时级内存/性能。本次无四麦声学模拟，仅格式码型和数值单元测试。

## 验证与交付

```text
python -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/test_diagnose.py
```

15项专项测试通过：uint64最大值与2^53以上编号、缺号/错误行、跨错误段不做相关、重启目录、配置冲突、单麦拒绝、零/常量/反相/相同通道、RMS整数平方溢出防护、输出目录保护、输入不变、CLI返回码等。证据见evidence/run01；不是重跑全部历史研究。
本次实现位于task/member-b-four-channel-receipt-01，基线3371aa23749026726e8588b9d8875defa7b3d726。只新增本目录文件，未提交/推送/合入。源码稳定后与实际输入回执集中交A，不逐次实验审批。
复核后是否归入活动入口按阶段收尾规则执行；当前不修改活动算法文件。
