# S1 本轮准备检查（2026-09-17）

以下表格保留初版准备检查的时间点。用户15:00构建后发现并修复辅助命令顺序误报，最新29项检查及真实产物只读核对见[修复记录](command-order-fix-01/README.md)。尚待用户Clean/Build，不将诊断替代构建或板测。

范围：用户选择修改原应用后的候选准备和主机自检。没有操作实际 Vitis/Vivado 工程，没有新ARM编译、下载或实板记录。不是独立复核或安全加载批准。

## 实际执行

| 项目 | 结果及原始证据 |
| --- | --- |
| 真实可移植 C 循环 + 外设模型 | 16项复用C1场景适配6秒目标 + 8项留存场景通过；[最终输出](evidence/model_20260917_132800_1ed703b5/1.stdout.log)、[命令/哈希](evidence/model_20260917_132800_1ed703b5/result.json)。 |
| 增量构建检查 | 21个 unittest 通过，含26个合同字段突变、链接参数负例、真旧对象拒绝、计时对象除数突变、内存边界，以及使用真实88个BSP文件/XSA/工具的临时候选前置检查；[输出](evidence/gate_20260917_133007_0f3d2885/stderr.log)、[命令/哈希](evidence/gate_20260917_133007_0f3d2885/result.json)。不能把临时候选/模拟ELF当作新ARM编译。 |
| 完整 main.c 语法 | 主机GCC、测试桩头文件、-fsyntax-only、-Werror通过；[结果](evidence/syntax_20260917_132802_dadb19ce/result.json)。不证明真实ARM/BSP链接。 |
| 实际旧应用前置拒绝 | 尚未安装S1的F盘原E1缺少新保存模块，预期拒绝；[记录](evidence/20260917_132858_pre_f9b781e368/failure.json)。没有修改其文件。 |

模型成功段实际保存288250组（包含完整停止尾包），逐组检查原始64位ID、四路整数及flags/reserved未改变。测试跨32位ID边界，复制前保持CPU_OWNED、成功后才FREE；容量精确边界/额外包拒绝、双保护区、坏包保留已验前缀、过慢复制溢出、DMA超时、独立重启均覆盖。模型时间和IO为模拟；实际新增复制耗时须由新板测日志核对，不能引用旧E1覆盖。

## 保留的失败及修复

- [首轮检查夹具失败](evidence/gate_20260917_132444_c10d148e/stderr.log)：旧对象路径少了 app/CMakeFiles；旧应用缺文件触发异常类型未匹配；整个对象的除数字节出现两次，不能全文件唯一匹配。修正为准确文件路径、明确缺文件拒绝、通过符号和已验证文字池偏移只修改实际计时除数。之后通过，未改golden或放宽计时断言。
- [真实依赖前置夹具失败](evidence/gate_20260917_132926_4fd61420/stderr.log)：AMD安装的 Vitis/gnu 为厂商目录联接，新增工具原始路径哈希检查被旧 no_links 拒绝。改为同时固定工具真实解析目标和SHA，再核验解析后的普通文件；不放开工程/输出目录的联接限制。最终21项通过。
- 其余早期通过记录同样保留；当前结论仅绑定上表最终源码/政策哈希，不能将多次运行累计为独立用例数。

## 复用与边界

- 源码基于 E1 冻结 proposed-src；无PL/BD/XDC/CIC改动。原11段耐久调度从本次候选移除，改单段固定6秒；所有权、包长8000、两槽8064、RX边界及正确计时函数保留。
- 检查器从既有 check_endurance.py 增量适配，复用 current_build 的ELF/安全读取、C1符号/加载读取及E1 timer_layout。**不安装、不宣称批准21c141b候选。**
- 本批固定参数为 S1_6S_RAW：288000最低组数，300000组容量，9600000字节数据 + 首尾各64保护；分配在既有程序区BSS，不改链接脚本/DDR范围。合同同时绑定源码哈希、真实对象和ELF、map边界、工具/BSP/XSA及生成的完整编译/链接命令。地址不按估算填写。
- 针对旧链接参数归一化问题，本批只支持当前固定路径，保留命令token大小写、顺序、全部 -Wl 子参数，不做路径折叠/吞掉参数；附加 -e/--defsym/--wrap 均拒绝。不是通用C解析器/加载器安全证明。
- 历史 check_entry.py/POLICY.json 依赖按本批POLICY哈希绑定，与E1历史 bbe39c38dc36ccb4c0492f492b86f6c46d885fbe 依赖一致；在当前共享目录存在但属未跟踪材料。缺失即报错，不回退到新待审版本。换机器/干净检出复现需按既有 E1 publication/reproduce.py 的固定提交提取机制提供该依赖；本轮尚未验证干净检出安装，不把本机可用说成通用可移植。

## 复跑命令

在本目录运行（以下均是主机检查，非Vitis构建）：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\run_model.py
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\run_gate_tests.py
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\run_syntax.py
```

每次生成新的 evidence 时间/UUID目录；保留全部错误输出。宿主编译器 F:/Program/env/mingw64/bin/gcc.exe。

## 未完成 / 下一步

用户备份并接入候选，Clean/Build；随后只读复核真实S1对象/ELF/map/Run加载，再安排单次连续实录。新BIN-串口关联检查适配、metadata/CSV/试听WAV、活动区间记录、独立读取器及最终交接尚待新录音；不能提前写通过。旧时序及E1实板仅引用，不重跑、不计入本轮。
