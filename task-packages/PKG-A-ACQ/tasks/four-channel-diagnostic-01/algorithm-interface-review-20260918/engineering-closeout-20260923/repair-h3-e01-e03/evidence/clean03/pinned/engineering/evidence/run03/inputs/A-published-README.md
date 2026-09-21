# A接口收口增量：逻辑确认与软件对照子包

本子包沿原任务继续。输入B f5a4cea、A e4f9eae3；固定快照与哈希在evidence/run02/bindings.json。没有提交/推送/合入，不重跑八段/run05/S1/计时/FFT/耐久，不修改one、候选RTL或B golden。

## 已交付

- A-CONFIRMATION.md：对错误恢复、身份、提交/TTL和固定4候选逐项确认，列未实现边界；不是生产冻结。
- source/logic_adapter.py：围绕准确A功能模型的独立accepted-row语义适配与舍入/提交决策函数；不是PS驱动或RTL。
- source/run_checks.py：从准确Git对象取得未修改模型、RTL快照、B framing/NPZ，生成实际检查证据。
- BUDGET.md：完整环节/生命周期清单，服务上界缺项写null，total仍REALTIME_BLOCKED。

## 本轮结果与边界

| 项 | 软件整数/模型 | 新AMD/XSim | 实际系统 |
|---|---|---|---|
| B八个合成分帧golden | 8/8 PCM、ID、row/interval/frame/reset描述符一致，跨250组包；未重跑S1大样本 | NOT_RUN | NOT_RUN |
| 原候选差异 | 实际复现clip不断帧、连续跳号漏检，两项expected counterexample保留 | NOT_RUN | NOT_RUN |
| 新逻辑适配 | clip/drop、连续错误、致命原因集合、停止重启、边界通过软件检查 | NOT_RUN | NOT_RUN |
| 固定RNE右移4 | 262401个S29整数案例与Fraction精确最近偶数舍入一致；正饱和/负边界/零化/越界拒绝 | NOT_RUN | NOT_RUN |
| mask/epsilon | 零、1/50平方边界、12有效bin边界、弱信号零化及单位检查 | NOT_RUN | NOT_RUN |
| 提交/TTL | 控制优先、等于/超过TTL、身份失配、未知available、溢出、重复提交及提交后晚错决策谓词通过 | NOT_RUN | NOT_RUN |
| 完整PHAT开方/归一化、IFFT/lag/DOA/DAS | 本轮NOT_RUN；只引用B来源 | NOT_RUN | NOT_RUN |

run01：28项通过，首轮软件记录。随后补齐提交后晚到错误的fail-stop分支、增加源码哈希和可选新输出目录，run02再跑28项，0意外失败；不是56个独立案例。run02为最终结果。两次记录均保留；预期反例是未适配候选的真实不一致，不通过修改golden掩盖。

## 复跑

在本目录PowerShell执行，输出必须为新目录：

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B ./source/run_checks.py --out ./evidence/run03
```

需要NumPy及本地存在准确A/B Git对象；缺失直接失败，不网络取替代版本。每项结果、失败traceback、来源快照、原候选反例、argv和源码SHA256均保存到新目录。退出0仅为软件自检，不是B独立复核。

## 剩余阻断与交回

当前没有新增RTL ready/valid/event背压或CDC仿真；accepted-row模型不能证明握手稳定、可综合性、在途错误时序或有限WCET。身份映射计数溢出、服务上界、实际算法缓冲容量/地址、生产桥和IP组合仍未落地。默认reference25不变；Q30与AMD24位twiddle绝不互借通过结果。PHAT阈值与fixed4的生产取舍仍待正式冻结。

这是可先交工作执行检查的**软件逻辑稳定子包**，不是完整工程收口。下一步由工作执行决定准确发布范围及B复核；若要实现硬件语义适配，先说明改动位置和用户操作边界。无需拓芙此时上板，不继续录音或扩展生产链。
