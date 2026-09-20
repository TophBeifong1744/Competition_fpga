# B1+B3：新gate前端与功率/状态边界验证

2026-09-21。**本轮节点验证及输入校验候选完成；原入口仍保留已发现的输入合同缺口，不签完整gate/FFT/AMD/生产格式通过。** 工作来源为收口分支b5913e596e28b30f9e04cf2c9ba365430b8914df内未改的fe67547算法。没有修改待审任务包、默认reference25、PHAT、Tracker、阈值或录音。

## 怎样做到不重跑FFT

verify_gate.py从准确integer_gate.stage的AST提取原有“均值/去均值/窗乘”和“半谱功率归一化”语句，替换返回值以暴露中间量。提取代码保存在run02/extracted-nodes.py，并绑定源文件SHA。没有另抄一份公式当作被测实现；原fixed_fft被替换为一旦调用就失败的guard，本轮调用数0。

期待值使用Python Fraction的精确有理数舍入生成，不调用原rne_div/rne_shift；状态oracle以精确功率比例和事件序列独立计算。Hann ROM与八份既有整数golden逐码一致，另固定1024个little-endian U32码文件SHA；这只证明ROM身份一致，没有独立证明cos生成算法或硬件ROM装载。

## 实际结果

| 检查 | run02结果 |
|---|---|
| 前端 | 13组1024×4输入：0/正负端点常量、1023:1端点比例且异常点位于窗首/中/尾、正负偶/奇均值半码；中间值逐码一致 |
| S25必要性 | 共8个测试窗码超出S24但处于S25范围；不得把居中窗输出夹回S24 |
| 窗乘RNE | 另4个正负半码舍入节点与Fraction一致 |
| ROM身份 | 八份冻结hann数组一致；hann-u18f17.u32le SHA256=51a05f855181f1774c3373c83085fd5a2792f5db932d66b1f3dc768e8ec6a2f2 |
| 功率 | 7组半谱：零、bin6/7/72/73、全S25负端点/正端点；sum/分子/分母/结果与有理数一致，带外为0 |
| 状态序列 | 4类事件（开启、保持、低于关闭、invalid）长度6的4096条序列逐步一致；加阈值序列共24840步，不称24840项独立测试 |
| 阈值边界 | 66组可表示U64的4n/2n±1、2/3/4路、连续4步，开启/保持状态分别核对 |
| U64不可达开启 | 2组超高noise，输入最大U64仍不能达到4n，未发生阈值乘法回绕；另8步单列，不包含24840步 |
| 非法输入 | 12种调用对比；严格候选全部拒绝；原入口错误接受7类，详见invalid-cases.json |
| 直接功率节点 | 6种非法半谱/窗输入由新checked_power拒绝；shape、整数类型、S25范围、窗范围/非零检查 |
| 原PCM入口 | 错误形状、浮点PCM、S24超界3种均拒绝 |

run01是第一轮结果，run02补充直接半谱及U64不可达开启边界；都保留，不累加两轮重复用例。前端期待/实际逐码通过后保存独立oracle数组至frontend-oracle.npz，输入及边界摘要见各JSON。run02源代码与结果由WORK-SHA256.json封存。

## 原入口发现的7类缺口及候选处理

原IntegerActivity接受整数值浮点noise、bool noise、负floor、小数floor、整数值浮点power、bool power以及非bool invalid标志。其中floor用int()截断再平方，会静默改变输入的含义。合法研究配置和整数码的既有结果没有因此被证明改变，不能将API输入验证问题称为原算法数值退步。

strict_activity.py提供独立候选：严格四路U64 noise/power，拒绝bool和float；floor必须为非负整数且平方可由U64表示；固定4/2/3/3/3配置字段类型与数值都检查；invalid必须为bool。合法输入仍调用原IntegerActivity，不改变计算或状态转移。checked_power只在暴露出来的节点入口验证形状/范围，仍执行原功率语句。

保留原“先验证power，再处理invalid”顺序：畸形API参数抛错，不声称已经实现实时fail-stop或恶意输入后的硬件恢复。该候选尚未替换旧stage/生产入口，不能把反例通过当新整链已经接入。

## 位宽结论与范围

对1024个S24码，精确和处于[-2^33,2^33−1024]，S34足够；RNE均值仍在S24。两S24之差绝对值不超过2^24−1，需S25；乘非负且≤2^17的窗码可用保守S43中间量，RNE>>17后仍在S25。实际可达范围及最小硬件位宽的进一步优化不在本轮冻结。

66个复bin的S25平方和，经精确左移45构成分子。run02逐项记录位值并执行原U104分子/U64输出界断言；没有执行FFT全动态范围验证。阈值4×U64必须允许最高66位，Python整数能容纳不等于硬件接口已正确分配位宽。

## 复现

```powershell
python -B F:/NUEC/validation/b-gate-b1b3-work/verify_gate.py --repo F:/NUEC/review-worktrees/algorithm-closeout-20260923 --out F:/NUEC/validation/b-gate-b1b3-work/run-new
```

CPython3.12.14、NumPy2.3.5；输出必须不存在。结果入口run02/result.json；所有合法状态/整数严格检查，没有浮点近似通过整数用例。仅元数据/ROM身份依赖原源码及冻结NPZ，不重跑旧研究。

下一步：B2+B4适配/数值profile边界和PHAT/IFFT接口保护；完整FFT动态范围、内部字宽、真实IP/RTL、晚状态及整链准入仍待做。正式目标存在/声学精度/收益不由这批整数节点测试证明。

本目录是下一稳定增量的独立工作材料，尚未提交或推送；不向正在审核的b5913e5追加实现，不自审自合main。
