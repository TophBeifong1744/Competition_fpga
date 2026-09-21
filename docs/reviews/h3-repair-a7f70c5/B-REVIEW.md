# H3-E-01～03 B 增量独立复核

实际日期2026-09-21。审核SHA：a7f70c5149a6503effdbbf16a9903d42c2d39e6d；远端分支codex/toph/h3-engineering-repair-20260921。原受检基线0abdc91c57787b7c868a797b88f35129de169faf，B反馈02f4ec23d771bd33a04ae3f297178ca34d537eb8。已fetch并直接查询远端精确匹配；独立短路径F:/NUEC/r/h3r固定该SHA，作者原件未改。

## 裁决：三项限定PASS

| 项目 | 本次独立证据与裁决 |
|---|---|
| H3-E-01 | ever_committed与可用性分离。原反例和CLIP/DROP/STOP/RESET交错后当前epoch晚错触发fail-stop，后续提交拒绝；显式start后的旧epoch回调审计但不杀死新会话。stop+error不吞追溯故障。关闭。 |
| H3-E-02 | 带类型递归冻结，首次成功submit绑定整会话；跨interval配置变更拒绝。深嵌套字典/列表、别名、键顺序及bool/int、list/tuple区分均核对；外部变更不改已保存快照，新session可换配置。关闭。 |
| H3-E-03 | 干净检出prepare从准确0ab/f879/02f对象导出132项，逐项与Git blob/当前受审源码核对；仓库外运行导出副本，无兄弟目录依赖。已有输出拒绝且字节不变；空对象库拒绝且不创建目标。关闭。 |

## 实际命令与结果

Python 3.12.14；以下python使用本机Codex运行时绝对路径，Git safe.directory只对该命令进程指定，未修改全局设置。

1. 在F:/NUEC/r/h3r执行 `python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/repair-h3-e01-e03/source/prepare.py --repo F:/NUEC/r/h3r --out F:/NUEC/r/h3r-out01`：退出0，PREPARED_EXACT_OBJECTS 132。
2. 从仓库外F:/NUEC/review-evidence执行 `python -B F:/NUEC/r/h3r-out01/run_checks.py`：10组、0失败、0错误。run/full.log及summary.json保留。原B反例在旧模型中仍成立，不能把其脚本退出0计为修复通过；修复断言来自10组独立执行回归及下面B新增检查。
3. `python -B F:/NUEC/review-evidence/h3-repair-a7f70c5/spec/probe.py`：20项独立边界检查全部通过；详见spec/results.json。
4. `python -B F:/NUEC/review-evidence/h3-repair-a7f70c5/entry_probe.py`：防覆盖、缺对象、132项准确导出绑定全部通过；拒绝原始stderr已保存。
5. `python -B F:/NUEC/review-evidence/h3-repair-a7f70c5/standards/check.py`：完整性通过。
6. 集成无冲突，518份工程文件逐字节与审核SHA一致。finalize.py从集成位置加载实际results.py、复用已校验导出测试，10组smoke通过；不累计为新的独立案例。

## Standards

无新增硬规范阻断。相对0ab仅443新增，原75份Git blob不变，范围外0；422项封闭清单及自身摘要匹配，另有20份发布说明/证据以Git绑定，不声称受422项清单覆盖。整个工程目录518文件匹配准确提交。387条历史绑定、129份唯一Git原件匹配，旧清单、B反馈、失败历史原字节保留。完整报告见standards/REPORT.md。

## Spec

无新增限定范围阻断。20项B新增检查覆盖8种撤销/晚错组合、4种旧epoch已提交/未提交回调、三epoch重复回调、stop+error、嵌套快照、配置类型和失败原子性。详细报告见spec/SPEC-REVIEW.md。这验证顺序事件Python模型，不证明真实异步或硬件行为。

## 批准范围及未测

本轮仅批准三项工程状态模型及复现入口返修，研究入口继续在repair-h3-e01-e03/；原75文件作为只读历史随修复保留，旧Results和旧run_checks不恢复为有效修复入口。未受影响的数值/FFT/预算检查复用02f4ec2中明确通过子项，不把原NEEDS_FIX整包当自动批准，不重跑FFT、耐久或采集。条件预算保持REALTIME_BLOCKED。

check_entry.py要求原工程/C候选工作文件，本机未运行该现场保护审计；已独立验证本次75旧原件和全部提交范围、防覆盖/缺对象，不代签A机器C候选或共享目录。作者深路径导入失败与同字节短路径复跑记录保留，本机短路径成功不宣称深路径限制已修复。ARM/BSP、PS C候选、RTL、CDC、实板、生产ABI、完整H3及实时均未批准。

规范轴阻断0项，需求轴阻断0项；H3-E-01/E02/E03在上述限定范围关闭。
