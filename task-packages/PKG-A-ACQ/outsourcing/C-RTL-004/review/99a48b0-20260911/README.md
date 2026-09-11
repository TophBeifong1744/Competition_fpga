# 004独立复核：功能通过，BD复现待修正

日期2026-09-11；精确输入99a48b0c52cc03cd2337c9db117e8261dfc2ab67，实现0457afc4e5666c490934a11823bd6a904e2a843c。原26项清单字节数及SHA-256复查全部匹配；作者submission未修改。

## 结论

整体状态 NEEDS_REVISION，不批准或合入004。规范/交付复现轴发现1项P2问题：BD脚本不兼容含空格的源码路径。功能需求轴暂未发现RTL问题；这不是完整形式证明。

- Vivado/XSim 2025.2（6299465）独立重跑原TB：1、3、默认32、64位，228次核对，1156 ns结束，全部PASS。已阅读包装映射、同步复位/clear/饱和规则与独立整数参考。测试平台沿前保持、沿后结果和原核心比较符合原操作单。
- BD：前两次受限环境无法正确建立路径，标BLOCKED_ENV；第三次非受限执行成功创建工程及导入设计源，但在导入TB时失败，未到Validate。此时是可定位的脚本复现问题，不归咎RTL。
- 作者既有BD默认32/3位日志仍保留其自检结论，不替代本轮独立BD验收。
- 综合、时序、板测、实际one接入：本轮NOT_RUN。

## P2：import_files的文件列表未保护含空格路径

文件 submission/scripts/rebuild_bd.tcl 第12行：

`import_files -fileset sim_1 [file join $package tb tb_stream_error_stats_bd.sv]`

传给Vivado的files参数需要Tcl列表；当前字符串在工具内部按列表解析，路径中的空格拆成多个文件。非受限原始错误：

`ERROR: [Vivado 12-172] File or Directory 'Beifong/AppData/Local/Temp/ss-c004-review-8c33c5fdc0b7474f9769a54757fd1b91/submission/tb/tb_stream_error_stats_bd.sv' does not exist`

该文件真实存在且原清单匹配。上一条sources_1导入使用list，已成功；TB导入没有list。修正建议见[唯一返工操作单](../../instructions/rework-01.md)，须实际重跑验证后才关闭问题。

## 执行与证据

仿真使用原 scripts/run_tests.ps1，VivadoBin=F:/AMD/2025.2/Vivado/bin，RunDirectory为新的包外c004-sim-review目录；成功日志见logs/simulation/。

BD第一次：原脚本，输出c004-bd-review/project，日志logs/bd/attempt1-sandbox.log。
第二次：将submission按字节复制到临时目录，仍在受限环境运行原脚本，日志attempt2-temp.log。
第三次：同一临时副本，不修改源码/脚本，解除执行限制后运行：

`vivado.bat -mode batch -source submission/scripts/rebuild_bd.tcl -log bd-unsandboxed.log -nojournal -tclargs project-unsandboxed`

工作目录：C:/Users/Toph Beifong/AppData/Local/Temp/ss-c004-review-8c33c5fdc0b7474f9769a54757fd1b91。原始日志见logs/bd/attempt3-unsandboxed.log。未重置TclStore或修改全局环境，仅缺失时临时补进程架构变量。

## 收尾边界

已阅读docs/phase-closeout.md。本次004未获整体验收批准，无新增获准源码，不进入rtl/tb/sim活动目录，不倒填9月10日冻结归档，不宣称阶段收尾完成。下一步由C按单修复，独立复核通过及指定复核人批准后再按阶段规则归位、在新位置验证和归档。001～003及主流程正在进行的收尾不受影响。
