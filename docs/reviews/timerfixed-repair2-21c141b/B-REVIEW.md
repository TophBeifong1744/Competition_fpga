# B 独立复核：TF-B-02-R1

2026-09-20。结论：**通过（限定范围）**。TF-B-02-R1 关闭；没有发现阻断。

- 审核 SHA：`21c141b223936730c2ce5139624fcedb412adafb`。
- 基线：`17afe32cebcff742bb2f9486388e91d9403f83dd`。
- 固定 B 反馈：`d1fd9d1db2be7ed292c17faf9dc9d27d407c9009`。
- 远端 Git 初次查询/获取因超时失败，改用官方 API 确认分支准确 SHA，逐个验证 Git 对象 ID；取得64个缺失对象后建立 detached 独立工作区。随后正常 fetch 最新 main 成功。
- 工作区：`F:/NUEC/review-worktrees/timerfixed-repair2-21c141b`；所有新增复核材料先存于包外 `F:/NUEC/review-evidence/timerfixed-repair2-21c141b`。

## 实际执行与结果

使用 Python 3.12.14、原生 Tcl `F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe`、MinGW host GCC `F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe`。以下 entry 均指仓库内 `task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/continuous-prototype-01/timerfixed-entry-01`。

```powershell
python -B "$entry/repair-02/verify_repair.py"
$env:TF_TCL = 'F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe'
python -B "$entry/repair-02/run_regressions.py" --phase fixed --out F:/NUEC/review-evidence/timerfixed-repair2-21c141b/required-run01 --gcc F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe
python -B F:/NUEC/review-evidence/timerfixed-repair2-21c141b/audit_git.py
python -B F:/NUEC/review-evidence/timerfixed-repair2-21c141b/spec/probe.py
```

1. 新267项、旧209项及最早87项清单均通过。独立从 Git blob 核对全部268个文件原始字节；相对基线58新增、2修改、范围外0。两份 originals 与基线相同；6份 B 输入与固定反馈原字节相同。未运行清单创建模式，旧清单没有重写。
2. 原82项及新增12项 Python 测试通过；loader组内14次真实 Tcl/Python/NTFS锁模拟通过，不能另计为108项Python测试。命令、cwd、退出码和完整捕获输出见 required-run01。作者运行器的输出标签仍含 AUTHOR，不是本报告结论的来源；本报告依据 B 在本机新执行的结果。
3. 四项原始反例均由 verify_link_output 拒绝；旧错误入口及宏/选项大小写负例通过。适配仅捕获诊断 norm 的 ValueError，原 gate 调用、反例和 GCC 探针不变；运行器检查真实状态，未把退出0当拒绝证据。
4. 独立 Spec 探针61/61符合预期：原4项、48项逗号/折叠/引号组合、4项合法路径正例、5项布局或额外参数负例。直接调用实际 gate，未复制作者断言作为唯一依据。
5. 本轮没有重新执行旧版本的四项误放行；其历史结果保留，并与固定 B 原记录逐字节核对。新版本的拒绝是在 B 本轮实际运行得到。

## Standards

未发现硬规则违例或必须修改项。两份修改文件、历史原件映射、B反馈身份和诊断适配均可追溯；失败记录未删。证据与未验证范围说明符合仓库约定。详见 standards/REVIEW.md 和 identity-audit.json。

## Spec

未发现遗漏、范围扩张或新的阻断。比较器先拆分 -Wl 逗号子参数，仅在紧邻 -Wl,-T 的位置规范化单一绝对脚本操作数；其他已知子参数布局严格匹配。完整 argv 比较保留顺序、大小写和分词差异。详见 spec/REVIEW.md、probe.py、probe-result.json。合法但不在归档布局内的 GCC 写法仍拒绝，属于明确约束。

## 允许范围与未验证项

仅批准 TF-B-02-R1 命令比较器修复与离线归档证据；结合原 TF-B-01/03 的限定结论，可将准确版本的 timerfixed-entry-01 候选入口按原申请范围入库。活动候选仍在本任务包，不替换 A 实际工程入口；历史旧版脚本和产物保持历史身份。

未运行完整现场 pre/post/load gate、新 ARM 编译/链接、真实 XSDB 下载或实板；未验证 XSDB 文件共享兼容性。GUI直接Run仍可绕过受检入口。本报告不批准M1/H3、长稳、整机或声学效果，不代签A共享目录同步。保留原件的空白提示不算检查通过。

Standards：0项阻断；Spec：0项阻断。发布和本机批次核对另见 PUBLICATION.md。
