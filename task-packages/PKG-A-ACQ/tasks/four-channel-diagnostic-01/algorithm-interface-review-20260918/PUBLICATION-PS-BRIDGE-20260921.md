# PS 语义桥 C 候选待审发布

实际日期：2026-09-21。仅申请独立主机 C 候选复核，不是生产接入或完整 H3 批准。

## 版本与范围

基于发布时 origin/main（949d7a0，完整父提交由本次 Git 提交记录确定）。候选原件在 `ps-semantic-bridge-candidate-01/`，1481 个文件；原清单覆盖1479项，清单 SHA-256 为 `e774f248f3995839f952db5c9d18eafeb3b7ece02f3897102cead1a65ace75b2`。原源码、失败历史和清单未改。

候选 README 的 main/f879/0ab 状态属于作者执行时快照。最新 B 结论见 `docs/reviews/a-h3-two-20260921/B-REVIEW.md`：f879 软件逻辑已限定通过；0ab 工程方案因 H3-E-01/02/03 需修改。本次不代为关闭这三项，不将依赖引用视为批准。请 B 重点独立检查 C 版历史提交事实、撤销后晚错、配置快照及跨 session 行为。

## 发布前复跑

`publication-ps-bridge-checks-20260921/`保存两次检查的原始根级命令、输出和汇总（并非完整数据输出副本；原始完整 run 目录在发布工作区旁保留）。run01为32/33：缺少未合入main的0ab工程方案工作文件，保护检查抛FileNotFoundError；其余检查通过。补齐准确依赖后run02为33/33，O0/O2各9组C自检通过。未改断言或测试源码。

ASan/UBSan缺运行库，未执行；ARM、BSP、实际异步和实板NOT_RUN，REALTIME_BLOCKED。主机sizeof不是ARM布局或WCET。

## 干净副本复跑（补充作者入口）

先取得准确提交对象 f879a54cf40359209895af955bcef92accdf79ea、0abdc91c57787b7c868a797b88f35129de169faf、f5a4cea7a7cf7dcccf09720cfff92131e6157752、e4f9eae3fe7e4104ff8a6827937e326954f90a82、b0643b11f6441c673d594fb40153567cceb37bd9、fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd。本发布父版本已经包含f879的增量文件；0ab未合入，需要仅在隔离副本恢复其工作文件，勿暂存或合入该依赖。

在干净独立检出、本目录工程方案路径尚不存在的前提下，从仓库根执行：

```powershell
$base = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918'
git restore --source=0abdc91c57787b7c868a797b88f35129de169faf --worktree -- "$base/engineering-closeout-20260923"
$task = "$base/ps-semantic-bridge-candidate-01"
python -B "$task/tools/seal.py" --verify
python -B "$task/tests/run_host.py" --cc '<本机GCC绝对路径>' --out '<包外不存在的新输出目录>'
```

如依赖目录已存在，先核对准确Git版本，不能覆盖他人改动。实际执行使用GCC 16.1.0及本机Python；准确路径、参数和退出码见commands.json。清单按原字节验证，建议检出时core.autocrlf=false。新增输出不要写入冻结候选内。只做发布完整性和复跑检查，最终独立裁决由B给出。
