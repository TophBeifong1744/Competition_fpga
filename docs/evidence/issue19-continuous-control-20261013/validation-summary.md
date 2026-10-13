# 准确候选验证摘要

七产品源内容ID：`f57493cf6d547d697f8430d3a3afa22a8a84c33d99e188936c46bcb85cd55f5a`。

| 原件运行 | 实际判定 | 全部冻结源匹配当前 |
|---|---|---|
| control-7 | FUNCTIONAL_SIM_PASS | True |
| export-1 | FUNCTIONAL_SIM_PASS | True |
| watchdog-2 | FUNCTIONAL_SIM_PASS | True |
| canary_export-1 | EXPECTED_CHECKER_REJECTION | True |
| full_probe-1 | SIM_FAIL | False |
| full_stop-5 | INTERRUPTED_FOR_FIRST_RESULT_DIAGNOSIS | True |
| full_stall-1 | INTERRUPTED_FOR_FIRST_RESULT_DIAGNOSIS | True |
| full_first-1 | SIM_FAIL | True |
| full_noise-1 | FUNCTIONAL_SIM_PASS | True |

局部控制、导出背压、watchdog及检查器canary按各自原件复用；不因包装重新运行。
full_first 的资格Fatal保留为SIM_FAIL；两次长测主动停止保留中断，不作PASS。
full_noise若通过，只覆盖三自然报告、至少两条实际转台命令、记录消费、一般在途STOP、保持STOP、warm恢复及新SID首结果。
9M整链、活动FFT/IFFT中STOP、默认4096 warmup、全板资源/STA/CDC、实板与PYNQ均未获得通过证据。
各运行完整配置、冻结源哈希、阶段与日志哈希见originals；范围判定见validation.json与review.md。
