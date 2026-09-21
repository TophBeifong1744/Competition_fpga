# 新增范围、运行与失败历史

实际日期2026-09-21；用户授权独立主机C实现，不操作工程。

## 先核查再实施

读取当前AGENTS/team-workflow、b064阶段增量、最新B节点复核与固定A模型/方案；远端main为fd1b99c，相关查询原输出见remote-status.json。B R1/R2已在fe67547获限定关闭，集中诊断b5913e5与节点349501c分别获限定批准；本轮不重跑/重修。没有发现本任务现成C语义桥或f879/0ab新的B批准，保留其受审身份。

实现独立ps_bridge.c/.h，参考f879 accepted-row行为而非修改原模型。旧C采集程序未读取写回、未接BSP。公共数值节点/窗口算法不在本轮范围。输出目录均新增，无覆盖。

## 实际构建命令

原样argv、cwd、exit_code、stdout/stderr路径和host_elapsed_seconds在每个run/commands.json。最终run04使用：

```text
F:/Program/env/mingw64/bin/gcc.exe
  -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror
  -I <run04/source> <run04/source/ps_bridge.c> <run04/source/host.c>
  -O0/-O2 -g -o <run04/host-O0.exe 或 host-O2.exe>
```

GCC版本原输出：`gcc.exe (x86_64-win32-seh-rev1, Built by MinGW-Builds project) 16.1.0`。两个构建均退出0，stderr空，9组C自检退出0；O0/O2不是18个独立测试组。Python/NumPy准确版本见invocation.json，所有参考由Git原对象导出并绑定SHA。

主机C单测包含27,131次断言（含逐行/内容循环），不将循环次数称为27,131个独立场景。外层33项中8个B合成帧golden、23个A模型对照输入、原反例1项、历史保护1项；同一案例在两种优化产物上复跑并比较输出，不重复累计。

## 失败与历次增量

| 运行 | 结果 | 处理 |
|---|---|---|
| run01 | 外层30项中28通过、2失败；C编译/自检通过 | B和A场景同名导致输出目录FileExistsError，未启动那两个A重放；failure.txt/tests.json及源码快照保留。是测试平台失败，不算C故障检出 |
| run02 | 30项PASS，C两优化自检PASS | 区分B_/A_目录；增加结果片段payload一致性、晚错事务审计和同时控制反例 |
| run03 | 33项PASS，C两优化自检PASS | 加INT32极值/高位错误码、实际极限计数、新session完整帧及sizeof断言 |
| run04 | **最终33项PASS**；C9组、每构建27131断言 | 增加提交和跨session拒绝审计、TTL=0和完整事件TRACE；最终源码对应run04/source，不用最终源码冒认旧run版本 |

开发时一次补丁因附带空hunk被工具整体拒绝，随后修正重试；没有写到其他任务路径，不是C运行结果。所有实际运行失败/中间证据均保留。

每轮尝试ASan+UBSan及单独UBSan构建，分别因`cannot find -lasan`/`cannot find -lubsan`退出1；最终原文在run04/006_build-asan-ubsan-stderr.txt和007_build-ubsan-stderr.txt。没有仪器化程序运行，明确NOT_RUN/UNAVAILABLE，不记为通过，不安装工具、不改环境。

## 核心反例真正触发

- 原A未适配模型接受clip窗口、连续缺号只记首个；C按f879拒绝该帧并记两个错误ID。原反例保存，golden未改。
- 输入8包满、输出2帧持有、结果4槽持有分别触发FULL；原内容/所有权保持，后续接收拒绝。
- 同批完成+错误，两种排列；另加RESET+fatal同时存在，均不提交。停止后回调、新session旧事务被拒绝。
- 提交后晚错及已经释放的当前session晚错均fail-stop；旧session晚错记录STALE，不误杀新session；审计中保留完整token。
- generation/row/frame/interval及TTL到边界实际走检查路径，无UINT回绕；审计满触发故障，ack不能清失败。
- length=0/31/8001/SIZE_MAX、空指针、侧带长度错、S24错误符号扩展、INT32_MIN/MAX、reserved/high flags均实际拒绝。
- ID>2^53及末尾UINT64_MAX帧逐码比较；偏移1字节的原始输入指针在C中实际使用；输入原缓冲随后污染，不影响内部副本。

## 复用/未测/封包

仅引用既有数值/声学/FFT/耐久证据，不运行这些任务；复用A/B分帧与语义golden是本轮C验证必需输入，不重新开发expected。seal脚本从准确0ab通用入口复用，仅修改新scope标签；不造另一套清单框架。

主机事件batch和同步clock hook只是软件合同。未执行ARM编译、BSP、真实寄存器/DMA、cache、CDC、Vivado/XSim、实现或上板；未测Cortex-A9 WCET。生产格式/ABI/时钟锚/失败恢复仍待独立方案，REALTIME_BLOCKED。不提交、推送、合入、修改阶段验收结论。
