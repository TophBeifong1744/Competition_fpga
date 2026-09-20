# 交 A 的集中复核提示词

请独立复核 B 的9/23算法侧候选收口。准确远端SHA以本轮发布回执为准，分支 `task/member-b-algorithm-closeout-20260923`；基线 `1f369dc688cc1e49d5b2b51735bce7dc9d1cfb78`。

沿用包：task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/
本轮入口：checkpoint-20260923/README.md
复用集中接口：28d5c775f15f29cbe1039e8ce60cc4498bb257b7（原21文件逐字节保留）
输入作者：94b5fe79d87e038e895878fb31030cded469bb33

先fetch并固定回执准确SHA，在独立检出阅读README、RESULTS、H3-ALGORITHM-CONTRACT、FORMAL-EVALUATION和HISTORY。Python3.12/NumPy2.3.5，在仓库根执行：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923/source/reproduce.py --out ../b-algorithm-a-review-new
```

输出必须在检出外新目录；勿覆盖作者音频/golden。当前SNAPSHOT清单核对完整父包+增量；父包旧封闭清单只按明确列项核对原件，不用它否定新增目录，不改旧清单。

请集中检查：

1. 三个门候选的码值/频带/标定来源、Run划分和持续时间状态；背景前以外没有参与标定。八段此前全被查看，所以probe不是独立验证集。频带活动不等于语音/目标身份。
2. 方向诊断是否保留零有效输出、目测偏差、拒绝分母、100/200/300ms敏感性与全部失败；是否把标记/混响不确定性留出而未作硬件校准。
3. 48WAV共同输入/增益/延迟/裁剪/量化/削顶；自动实际全回退单麦，不声称增强；同源播放WAV未用作虚假SNR参考。
4. 新整数gate+旧DOA链8真实探针120数组；约0.389%浮点/整数功率差异仍保留。不是AMD全链逐码、不代表全八段整数/全动态范围通过。旧run05等已批准未受影响项引用，不重跑。
5. 全包失败历史、依赖及原21文件身份；新增代码只在本轮目录，没有修改默认算法、采集或工程。
6. 按H3-ALGORITHM-CONTRACT.md回填工程映射、最终profile裁决、缓存生命周期和完整周期预算。当前8FFT+6IFFT只是算法调用数；103364只是历史槽算术，不能作为实时证明。

可独立先裁决可移植研究工具、结果归档及整数合同草案；本批不申请正式目标存在/方向/音频收益、M1、完整H3或整机通过。若阻断请保留反例和准确SHA，反馈B修复，不合并。通过后仅按批准范围合入、相称回归和batch-closeout；不要自认B作者测试就是独立批准。

A-MINIMUM-INPUT.md仅针对正式缺口：先核实现有同步重复播放/完整留存能力；无需重录原八段、重复FFT/耐久或C新增任务。A本机共享未提交帧适配/Skill等保留，不夹带、不代签同步。任务分支和开发工作树在研究/复核未结束前保留。
