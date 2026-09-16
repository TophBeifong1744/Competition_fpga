# TF-B-02-R1 修复候选

2026-09-16。结论：作者修复和离线回归通过，**待 B 独立复核，不合入 main，不部署实际工程**。本轮无新的实板操作或验收门槛。

## 输入与范围

- 原分支：`codex/toph/timerfixed-entry-20260916`；准确基线 `17afe32cebcff742bb2f9486388e91d9403f83dd`。
- 直接远端确认 B 反馈分支 `review/member-b-timerfixed-bbe39c3`，准确提交 `d1fd9d1db2be7ed292c17faf9dc9d27d407c9009`。
- 先读该提交 `docs/reviews/timerfixed-repair-17afe32/B-REVIEW.md` 和 `spec/REVIEW.md`；两份报告、两份反例脚本和两份原结果以 Git blob 原字节保存于 `review-inputs/`，来源和 SHA 见 `PROVENANCE.json`。不修改 B 分支或反馈。
- 唯一生产实现修改是 `command_contract.py`；根 `README.md` 仅追加最新入口。其 17afe32 原字节保存在 `originals/`。其他新增内容均在 `repair-02/`。
- `check_entry.py`、封存锁/keeper、Tcl、实际源文件/ELF/bit/init、POLICY、旧测试和全部旧证据保持原字节。共享目录仍引用原入口，本轮不覆盖该引用，也不修改 F 盘 one 或 Vitis 应用。

## 根因与修复

原实现对整个 `-Wl,` 后缀使用 `ntpath.normpath`，使 GCC 逗号分隔的多个实际链接参数有机会被 `..` 折叠吞掉。本轮先经现有 Windows argv 解码，再对 `-Wl,` payload 按逗号拆分；**只有已经确认是链接脚本路径的单个操作数**才能做路径规范化。

本比较器明确只支持已归档布局：

1. `-Wl,-T` 后必须紧接一个 `-Wl,<绝对脚本路径>`；后者恰好一个非空子参数。未知组合、插入选项、额外逗号、缺操作数、相对/无归属路径均拒绝。
2. 原 `-Map=memory.map,--cref`、原库分组及结束分组按子参数列表严格识别，原始内容/顺序不变；未知布局、库大小写或次序变化不作等价归一。
3. 前端选项、宏名/值、引号形成的 argv 边界沿用原语义；不通过去掉参数或笼统忽略差异通过比较。

这里不是通用 GCC/ld 参数解析器。即使 GNU ld 另有合法写法（如 `-Wl,-T,<path>`），本候选也拒绝，新增布局须另行审核。路径大小写、斜杠、`.`/`..` 和等效外层引号的合法变体已有正例；引号不会使 `-Wl` 内逗号变成路径字符。

## 本轮实际执行

完整命令、cwd、返回码和输出在 `evidence/baseline-01/`、`evidence/fixed-01/`。复现时创建包外新目录，不覆盖这些原件。

| 项目 | 实际结果与含义 |
| --- | --- |
| 修复前四个 B 反例 | `ACCEPTED` 全部复现；新增测试在旧版失败，保留原输出，状态明确不是修复通过 |
| 修复后四个 B 反例 | 最小 `,-L,/../lscript.ld` 及额外 `-e`/`--defsym`/`--wrap` 均被 `verify_link_output` 拒绝 |
| 新测试 | 12 个 Python 方法通过，含上述四项、合法路径/引号正例、未知布局/空项/顺序/大小写/宏值/边界拒绝 |
| 原测试 | 原 18 + repair-01 的 14 + loader 的 6 + 父包 10 + safety 34 = 82 项通过；未修改旧测试 |
| 实际 Tcl 模拟 | 原 loader 组产生 14 份 case 记录；真实 Tcl/Python管道、NTFS锁和归档ELF，硬件调用及部分完整gate条件仍是模拟 |
| 原 B 四个负例 | 原两个错误 ELF 入口拒绝，两个 GCC 选项大小写判为 DIFFERENT；未使用错误 ELF 上板 |
| 主机 GCC 参数探针 | 使用本机 MinGW GCC 的 `-###` 打印子进程参数，退出0且不生成程序；不是 ARM 工具链新编译/链接 |

合计 **94 项 Python 测试方法**，14 次 Tcl 模拟包含于其中 loader 组，不能另加成 108 项 Python 测试。此前 B 的独立 guard/keeper 补测不属于本轮新执行，不能计为本轮通过。

### B 脚本适配与结果判定

`spec/extra_link_flags.py` 原字节直接执行，其脚本返回0不足以判定修复；运行器额外逐项断言状态为 REJECTED。

`spec/check_arguments.py` 原先在生成诊断字段时直接调用 norm，严格拒绝会抛出 ValueError、阻止其写报告。本轮仅在**包外副本**将该诊断 norm 包装为捕获 ValueError 并输出 `REJECTED_BY_PARSER` 标记；gate 调用、所有反例、原始 argv 和 GCC 探针不变。确切替换前后文本及原文件 SHA 在 `adaptation.json`，适配副本也随结果保存。运行器检查真正的 `verify_link_output` 拒绝结果，不拿诊断标记或退出码代替它。

原 repair-01/reproduce_b_negatives.py 的既有期望适配照旧复跑；它仍保留 B 原脚本，未改原文件。本轮无新增意外测试失败；故意运行旧实现产生的回归失败、旧 repair-01 的失败历史均保留。

## 完整性与复跑命令

旧87项和209项清单保留原字节；209项按 `command_contract.py`/根 README 的 originals 映射逐项核对，其他209集合文件原路径不变。旧 `repair-01/verify_repair.py` 是17afe32封闭集合检查器，不能在新增repair-02后直接当本轮入口或重建旧清单。新入口：

```powershell
# 在固定新 SHA 的独立仓库根，python 为本机 Python 3.11+。
$entry = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01'
python -B "$entry/repair-02/verify_repair.py"
# 如 Tcl 不在作者默认位置，设置成 B 本机的原生 tclsh.exe。
$env:TF_TCL = 'F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe'
python -B "$entry/repair-02/run_regressions.py" --phase fixed --out F:/NUEC/review-evidence/timerfixed-r1-new-run01 --gcc '<本机主机GCC绝对路径>'
```

输出目录必须不存在；以普通用户环境运行 NTFS 锁测试，沙箱权限拒绝须保留失败后在同字节版本复跑，不能放宽锁。不要运行 `--create` 重写清单或把 `--phase baseline` 用于新实现；基线仅在固定17afe32的副本复现。

原件恢复位置：本轮两个修改文件在 originals，前一轮三个修改文件仍在 repair-01/originals；完整原树分别由17afe32、bbe39c38恢复。新 `R1-SHA256.json` 是本轮精确文件集合（不含自身），原制品未格式化，不删除历史证据。

## 未执行与允许结论

本轮未运行完整现场 pre/post/load gate、新 ARM 编译/链接、真实 XSDB 下载、RTL 仿真、综合/实现、板卡或长稳；未测真实 XSDB 文件共享方式兼容性。GUI 直接 Run 仍可绕过受检加载入口。采用 xilinx-suite 的范围边界区分工具探针/归档检查/模拟和实板，不能互相替代。

只申请 TF-B-02-R1 检查器修复及离线证据复核，不冻结新数制、不改采集/硬件/算法，不新增 M1/H3 或阶段门。TF-B-01、TF-B-03 仍沿 B 之前的限定结论；本轮作者回归不是 B 新批准。

共享 main 和其他任务脏改动保留；发布只更新原待审分支，不合并、不推 main、不代签共享目录/B电脑同步、不清理仍被实际工程引用的文件。完成后将准确新远端 SHA 交 B，批准前保留工作树及所有原件。
