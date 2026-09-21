# A复核R1/R2返修：只审检查器增量

A原结论 **NEEDS_FIX，不批准整包合入**；本轮为B作者返修，不自签关闭、不合main。读取用户提供的REVIEW.md后，在原任务分支/原包继续；远端main刷新仍cf026cf。A的原报告以原字节保存为 [A-REVIEW-original.md](A-REVIEW-original.md)，SHA256 `13fab2584b5e16ac9c367a207871723f204f8280d8d142d4e89b13160b25dbd8`。用户只提供报告，未提供A的probe.py、probes JSON及comparison.json；本轮根据报告描述复建两条反例，不冒称收到这些A文件。

## 实际修复

| 项 | 修改 | 增量证据 |
|---|---|---|
| R1 | 为每事务记录外部必需status在捕获`now`上的可见时刻；全部完成后以其最大值约束available下界，继续允许延迟提交 | A所述available=0/最后ifft=2反例拒绝；同拍/晚提交/中间available/TTL等号允许；未来、过期、未完成后级、借用别帧完成时间拒绝；新session重启时间及uint64最大值通过 |
| R2 | source_sample排除bool/float且显式有符号profile域；输出available严格uint64。所有有效拍先校验类型再作背压等值比较 | A所述source=0.0/available=8.0拒绝；float/bool/越界、首次/持续/恢复接受拍类型变化拒绝；startup负编号及原PCM不变 |

`trace_scoreboard.py`是唯一修改的执行源码；数值模型、预算、run05及旧check_delivery原件不改。新增验证/运行/交付检查脚本位于本子目录。43项期望中34项拒绝、9项允许；合法轨迹的结果还与原checker严格比较。测试只加载checker和原JSON夹具，不导入FG/DAS/FFT/声学模块。

实际执行先在原实现上产生 `before/`、`before.log`、退出1；两条A误接收及指定18条旧误接收均复现。修复后 `after01/` 与日志退出0；最终绑定源码的运行见 `validation01/runner.json`、`run.log`、`checks/result.json`、`delivery.json`。最终43项均符合预期，完整命令/源码/输出SHA保留；前后结果不互相覆盖，不累计次数。

## 新入口（只跑增量）

在准确候选Git检出根，Python3.12.14，不要求NumPy（未导入数值模型）：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/repair-r1-r2/run_repair.py --repo . --out <不存在的新目录>
```

必须具有 `d3d2a3d`、`dbd7ab5` 原Git对象，以便直接读取旧checker并校验旧证据；不依赖微信目录或兄弟worktree。独立交付检查可运行同目录 `check_repair.py --repo . --run <上述输出> --out <新结果.json>`。输出禁止覆盖。

旧 `check_delivery.py` 有意保留对旧run05源码的精确绑定：在返修源码上它会报旧checker哈希不匹配，这是版本变化，不是放宽哈希或改旧清单的理由。新 `check_repair.py` 验证新运行源码哈希、原A报告、原baseline中除6个明确可变文件之外的所有文件原字节。原run_all只用于旧完整包/需要扩大数值验证时，不作为本返修的必跑入口。

## 已检查部分复用、集中裁决落实

- A已实际复核的1215个CORDIC向量、S28包含界、RNE/饱和/32点PCM、预算分账及未受影响反例直接复用，本轮运行次数0。不把原整包NEEDS_FIX改成PASS。
- CORDIC独立身份 `cordic-s23-normalized24-canonical-q8-v1`：配置 `cordic-profile.json` 与摘要绑定不变的候选源码、旧FG依赖及独立CORDIC golden文件；旧FG/reference25不变。S28仅包含界，≤1 Q8码仍为确定向量结果，不是全域误差定理。
- A已接受8前视/17历史、最多两beam+最新pending、20ms平滑回mono为下一步研究取舍；这不批准生产，也不倒签旧9前视实现。
- session物理采样时基统一；硬停沿fatal/session_abort语义，不能使用音频平滑STOP代替。真实CDC、捕获时钟、异步状态可信性仍需A工程验证。
- ROM优先评估PS DDR，地址/所有权/cache/有限服务仍未给；REALTIME_BLOCKED及不同容量口径保持。未修改one/Vitis、A/C或声学研究。

当前需A只复核R1/R2及邻接边界，优先一个工作日内给结论或预计时间；通过之前保留待审分支/全部证据。准确返修提交及复制提示词见父目录A-REVIEW-PROMPT/DELIVERY发布补记。
