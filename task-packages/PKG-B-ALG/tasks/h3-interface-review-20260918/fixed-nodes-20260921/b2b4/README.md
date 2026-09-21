# B2+B4：适配、PHAT与IFFT边界增量

实际日期2026-09-21。节点验证及独立保护候选完成，原实现/默认算法不改；不签全动态范围、AMD、完整H3或生产合同通过。来源为b5913e5收口分支内未改变的fe67547算法，完整文件SHA在run01/result.json。

## 实际执行

| 检查 | 本轮结果与依据 |
|---|---|
| 固定RNE右移4 | 33个S29端点/正负半码/±1邻域；与Fraction理想舍入、S25饱和和计数严格一致；最大正端附近确实触发饱和，不可仅截位 |
| 单蝶形 | 从原fixed_fft AST提取复乘节点，32个25/29位组合；独立有理数检查复乘RNE及蝶形/2、饱和，4次分量overflow正确记录。不是全FFT或真实全部twiddle ROM覆盖 |
| 开方 | 26个零、小平方、中点邻域与大数（最高约150位）输入；Decimal100位精度oracle最近整数一致 |
| 倒数表 | 256项LUT与独立Fraction RNE逐码一致；没有据此声明倒数全域误差界已证明 |
| PHAT归一化 | 207个非零互谱（四象限、小量、S25端点组合），与高精度理想归一化舍入最大差0码；零互谱单独拒绝。测试前限定误差≤2个输出码，实际0，不扩展为任意输入定理 |
| mask/epsilon | 49/50/51倍幅值比较覆盖1/50阈值两侧及等号；bin6/86大幅值不进入band最大值；零/11/12有效bin判定；epsilon严格为2^26/10^15互谱幅值码，介于0和1，不改为0 |
| 四路上游故障 | 对0/11/12-bin三组逐个注入4路任一路overflow，共12次原PHAT入口全部拒绝，mask清空 |
| 共轭补谱 | 511个镜像位置实部/虚部符号正确；通用接口三类非法输入现状与新保护见下 |
| 现有IFFT错误汇总 | 提取checkpoint/golden.py原any-overflow语句，6个pair逐一注错均使全部lag无效；不执行IFFT |
| 完成协议模型 | 仅独立FrameGuard候选检查状态未齐拒绝提交、stop优先、正常唯一提交、重复提交拒绝、提交后晚错记录并失效。未绑定真实status/TLAST接口 |

全FFT/IFFT调用均为0；完整变换入口设调用即失败guard。没有新录音、声学模拟、旧研究回归、AMD仿真或实板。输入向量为数学节点夹具，未产生音频。

## 三类通用补谱保护缺口

原conjugate_complete只检查形状，接受：

1. DC虚部非零；
2. Nyquist虚部非零；
3. 内部频点虚部为−2^24，镜像取负后得到+2^24，超过S25最大正码。

guards.checked_conjugate检查整数类型、S25范围、实信号DC/Nyquist要求及取反溢出，对三类输入均拒绝。**当前PHAT有效输出通常不会达到最负S25值，不能把通用接口反例当作八段实录已发生故障。** 原模型不覆盖一般非法输入这一事实保留，候选不静默限幅后继续。

guards.checked_adapter另要求四路513×2半谱、整数S29；原适配内部int()转换并不是接口域验证，新候选拒绝浮点、错误形状和S29超界。候选尚未替换调用处。

## IFFT状态结论的边界

现有checkpoint实现先完成Python调用后汇总overflow，6次注入验证的是这条既有逻辑。它不是硬件异步完成状态协议，不覆盖晚TLAST/status、背压、跨session事务或输出设备。

FrameGuard是可执行建议，不是原checkpoint现状；提交后发现错误时保留COMMITTED历史并记LATE_ERROR_AFTER_COMMIT，同时设置invalid。无法物理撤回已输出样点，不宣称它能消除事后故障。实际结果提交/同拍优先级还需A集成协议及独立测试。

## 精确身份、复现和未测

```powershell
python -B F:/NUEC/validation/b-gate-b2b4-work/verify_nodes.py --repo F:/NUEC/review-worktrees/algorithm-closeout-20260923 --out F:/NUEC/validation/b-gate-b2b4-work/run-new
```

CPython3.12.14、NumPy2.3.5；输出必须不存在。run01内result.json、adapter-cases.json、mask-cases.json、normalization-cases.json保存结果与严格期待值；butterfly-extracted.py保存原节点，OUTPUT-SHA256.json封存输出，工作源码由WORK-SHA256.json封存。

未测：整个FFT/IFFT动态范围、全互谱域误差证明、全部mask/稀疏子集、硬件内部字宽、AMD逐码、实际status协议和生产接入。portable Q30和AMD24位twiddle没有互借通过。

下一步可进入B5+B6的lag/DOA/DAS节点边界验证；同时将B1–B4已发现的输入保护合为一个待集成候选，不能把“本地保护模型通过”写成“原链已修复”。本工作区尚未提交/推送，不向正在审核的收口分支追加实现。
