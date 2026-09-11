# C-RTL-004-R1：修复BD恢复脚本的空格路径问题

2026-09-11；本批只有这一项返工，仍属004，不新建005，不做开放式研究。原任务接口和器件不变。

## 直接按步骤完成

1. 从包含99a48b0完整交付的现有C分支继续。保留原日志和原清单副本，不改001～003或RTL核心。
2. 修改 submission/scripts/rebuild_bd.tcl 中的TB导入为：

```tcl
import_files -fileset sim_1 [list [file join $package tb tb_stream_error_stats_bd.sv]]
```

   同时检查本脚本其他文件列表参数是否有相同问题，只修路径传递，不改端口、时钟、接口或算法。未验证前不能声称这行修改已解决全部复现问题。
3. 在新的包外目录复现；让源码所在路径至少含一个空格，如临时目录下的 C004 source/submission。用实际Vivado2025.2执行原README恢复入口，目标工程目录也用新的包外目录。不要操作共享one工程。
4. 必须实际得到 SOURCE_TYPE_PASS、PORTS_PASS/VALIDATE_PASS（默认32和修改3位）及 ALL BD TESTS PASS；保留所有警告和原始日志。失败则保留首错并反馈，不重装工具或重置全局设置。
5. 成果仍集中在 submission/。新增 logs/rework-01/ 存放本次日志和端口表；README增加修正版本、准确提交及命令。原始失败记录保留，不用新日志覆盖旧日志。
6. 原 file-manifest.json 先原样保存为 evidence-history/manifest-before-rework-01.json，再重建当前清单（不含自身）；说明源码与日志版本对应关系。无需复制整个旧工程。

## 不需要做的事

不改包装、原核心、TB行为；只修BD恢复脚本时，不要求重跑已通过的228次功能仿真。不补GUI截图、不新增综合/布局布线/板测、不领取005。若确需改RTL/TB，先报告原因，不沿用旧功能PASS。

## 交付及验收

提交并推送到既有 codex/c-rtl-001-outsourcing-docs，提供提交号、submission目录和复现命令。不自行合并main。复核方会在含空格路径独立恢复BD，成功后再处理正式批准及活动目录集成。
