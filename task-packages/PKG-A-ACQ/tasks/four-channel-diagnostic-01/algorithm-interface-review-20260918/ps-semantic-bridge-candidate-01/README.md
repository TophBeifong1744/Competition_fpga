# PS语义桥：独立主机C候选

实际执行2026-09-21。完成主机C候选及自检，可交工作执行发布待审SHA；**不是B独立批准、ARM/BSP集成、实板或完整H3通过**。本轮仅新增本目录，没有修改one/Vitis、旧待审包、算法或录音。

## 来源/复核状态

- 当前本地和直接远端main：`fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd`。
- B接口：`f5a4cea7a7cf7dcccf09720cfff92131e6157752`；A语义：`f879a54cf40359209895af955bcef92accdf79ea`；工程方案：`0abdc91c57787b7c868a797b88f35129de169faf`；协调：`b0643b11f6441c673d594fb40153567cceb37bd9`。
- B R1/R2、集中诊断和固定节点已获各自限定离线批准，不再按bb964cb旧退回状态派修。A f879/0ab仍未查到B批准，不把发布当批准。准确输入快照见evidence/run04/inputs、bindings.json。
- f879和0ab发布文件逐项保护核对见preservation.json；仅显式允许文本CRLF等价并保留两份原字节哈希，未写回原件。

## 本轮实现

`src/ps_bridge.h/.c`：字节解码LE H1、错误行ID基准、完整原因位集、恢复切段、N1024/H512、8包自有副本、2个帧槽、4个结果槽、有限代次、状态屏障、TTL、同批控制/错误优先、提交后晚错及旧会话回调审计。无malloc、无Xilinx头文件、无算法运算、无真实DDR地址。

配置/时钟均显式注入。测试使用的TTL=512和required_status=3只是夹具，不是生产默认。S23F20、8/9 lookahead、数值profile与最终ABI仍按集中裁决；本候选不实现这些算法字段。

| 验证 | 最终run04 |
|---|---|
| GCC 16.1.0，C11，O0/O2 | 两次严格编译成功；Wall/Wextra/Wpedantic/Wconversion/Wshadow/Werror，0警告 |
| 原生C测试 | 9组，每构建27,131次断言；包含所有权、同时事件、晚错、满队列、计数、TTL、长度边界 |
| 外部对照/保护检查 | 33项PASS，0失败；其中8个B合成golden，23个新增A模型输入场景，原反例及原包保护各1项；不累计O0/O2为不同案例 |
| 数据/描述符/错误事件 | C输出与准确A模型/B NPZ比较，ID超过2^53及UINT64_MAX不经浮点；两构建结果逐字节一致 |
| ASan+UBSan / UBSan | 链接器缺libasan/libubsan；NOT_RUN，不计负例通过，不安装工具 |
| 存储 | bridge sizeof=178856B、align=8；详细组件及生命周期见MEMORY.md |
| ARM/BSP/板测/真实异步 | 全部NOT_RUN；REALTIME_BLOCKED |

完整编译/运行argv、版本、stdout/stderr、退出码和主机观察时间在run04/commands.json。原始输入、帧文件、事件、comparison.json均保留。run01两项测试平台目录冲突失败及run02/03中间证据不删，见HISTORY.md。

## 一条复跑

仓库根运行，输出必须是不存在的新目录；只需要现有主机GCC、Python+NumPy和准确Git对象，不需F盘工程/BSP。

```powershell
$py = 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$task = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/ps-semantic-bridge-candidate-01'
& $py -B "$task/tests/run_host.py" --cc 'F:/Program/env/mingw64/bin/gcc.exe' --out "$task/evidence/review-new"
```

运行从Git原对象提取A/B参考，不用本候选生成expected。B synthetic输入须先匹配原raw SHA，再比较原NPZ与描述符；原S1大数据不重跑。代码运行快照也随本轮输出保存，不把后来源码冒认成旧运行版本。

封包脚本复用0abdc91的通用seal.py；`python -B <本目录>/tools/seal.py --verify`校验PACKAGE-SHA256.json与MANIFEST.sha256。封包后复跑请输出在包外，以免新增文件破坏封闭清单。

## 评审入口/停止点

- [CONTRACT.md](CONTRACT.md)：API使用、接受点、状态/控制、错误恢复和候选边界。
- [MEMORY.md](MEMORY.md)：sizeof、容量、积压、所有权和剩余生产阻断。
- [HISTORY.md](HISTORY.md)：实际新增、失败、复用、工具缺口。
- `evidence/run04/summary.json`：最终结果；`tests.json`及完整原始日志供复核。

到此停止。未提交、推送或合入；工作执行检查完整性、发布准确待审SHA后交B独立复核。下一步若要修改Vitis，仍先由拓芙选择应用/副本并亲自操作。本候选没有解决真实异步硬件时序、PS WCET、DMA/缓存/DDR合同或H3准入。
