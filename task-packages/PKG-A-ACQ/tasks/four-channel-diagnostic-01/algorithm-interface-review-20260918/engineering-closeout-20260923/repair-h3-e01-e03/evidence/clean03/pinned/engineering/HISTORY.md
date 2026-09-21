# 执行、失败与复用记录

实际日期2026-09-20；目录名20260923是检查点标签，不倒签。

## 来源核查

读取AGENTS、team-workflow、9/18复验/八段复验入口、CONTINUE、B集中回复、f879 README/A-CONFIRMATION/BUDGET。本地main为1f369dc，未切换共享工作树。最初沙箱内git ls-remote遇schannel `SEC_E_NO_CREDENTIALS`；经允许的只读网络查询成功。该错误为环境查询失败，不是算法失败；原工具输出在会话，最终成功原始stdout/exit_code保存evidence/remote-heads.json。

发现bb964cb新B合同后将新gate额外4次FFT和两套窗纳入预算；随后发现5e343f2复核要求B修复R1/R2，原报告从准确Git对象保存在run03/inputs/B-new-review.md。没有重跑/抢改B全包，没有据该状态类局部自检宣称B返修关闭。未找到f879独立批准，继续标受审。

## 实际命令与历次输出

解释器绝对路径和工作目录见各run/command.json。共同入口为 `source/run_checks.py --out evidence/runXX`（实际从仓库根提供完整任务相对路径）。run02、run03追加 `--inspect-ps F:/College/verilog_digital_system/Vitis/four_mic_endurance/src/continuous`。

| 次数 | 退出/结果 | 用途 |
|---|---|---|
| run01 | 0，17项PASS | 初始数学/所有权/预算；发现并留存非实端点输入未被B函数拒绝的预期反例 |
| run02 | 0，21项PASS | 增加候选IFFT守卫、overflow、新gate状态、身份/内存反例，保存实际PS只读快照 |
| run03 | 0，21项PASS | 最终版：补全lag两个除法/DOA残差/延迟生成操作预算，重复错误不产生空interval，真实时间倒退拒绝，绑定新B返修报告 |

21是最终测试组数量，不将17+21+21累计成独立测试数。run01/02源文件哈希在各自command.json，不借最终源码声称能逐字复现旧日志；最终可复跑源码对应run03。没有删除失败/反例，也没有发生未预期的测试失败。预算公式修订是代码检查发现的漏项，非“旧预算已通过工程验证”。

## 保留的可复查反例

- endpoint-counterexample.json：非法DC imaginary=1被B补共轭函数接受；修复候选独立守卫拒绝DC、Nyquist、负最小共轭溢出。该非法输入不来自实录、不代表已有正常PHAT输出坏了。
- IFFT相位对齐极值输入：独立DFT证明输出超S25，portable模型报告255次overflow；期望是整帧/配对失效而非擦除计数。
- 8包逻辑队列的缩小单槽反例：满后不覆盖旧包，保留CPU所有权，后续arm拒绝；另离散模型服务慢于到达最终QUEUE_FULL。
- unbounded service明确拒绝；保守串行预算超限并正确保留REALTIME_BLOCKED；较快假设同样不解除生产阻断。
- TTL、frame/interval计数、配置错配、旧epoch晚到、postcommit错误、重叠/越界/未对齐内存布局均保存预期拒绝结果。

每项原始结果/异常traceback能力在raw.log与results.json，不另造“真实硬件失败日志”。本轮没有上板或工具仿真失败可归档。

## 引用但未重跑

f879的28项与262401个fixed4案例、B run05、八段/S1/计时/耐久、FFT29扩展和BRAM OOC均只复用准确来源与原边界。29个f879发布文件保留原raw hash并比较Git内容（仅文本CRLF等价显式记录），没有改清单或原证据。新3个inverse基向量不算旧FFT全包复跑，也不能推广AMD24位twiddle。

未执行：生产C实现、RTL、AMD IP/XSim、布局布线、CDC、板卡、声学指标和完整H3。与B独立复核、工作执行发布严格分开。
