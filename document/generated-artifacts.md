# 文件分层与受控清理

活动维护源：project/rtl、simulation/tb、models、software、data/fixtures及实际工程的必要IP/BD/XDC/初始化/描述。每份活动源一个权威入口；不强搬当前厂商工程，也不把旧task-packages当新活动工程。

历史合同/冻结证据：docs、archive、deliverables、task-packages按原路径保留必要材料和链接。原始样本、尚未接入或待审候选、不可重取波形和量化依据不得按重复/旧/大/ignored删除。

运行输出：codex_out、simulation/work和真实厂商run。失败以总结为主，仍需诊断/难重取/定量复核才留最小充分原件；已结清无用途缓存无需永久存档。WCFG是显示配置，不等于大型WDB；.xpr/.bd/.xci/.mem、必需DCP/bit/XSA/ELF/HWH不按后缀归缓存。

清理顺序：只读盘点→逐对象核绝对路径和reparse/link→确认无占用、独有成果、开放PR/未结诊断/报告引用依赖→确认所需摘要/实际文件可取→执行准确对象→核残留和引用。失效worktree注册可在保存提交定位后prune，不删除对应分支/提交。远端短分支只在准确成果已保存、无开放PR/在途用途且删除权限明确时删除；旧Release资产先核引用，不批量删除。

本次清理实录见原#23及codex_out/m-workflow-overhaul-20261013/CLEANUP-RESULT.json。此路径是操作证据，不是任务状态数据库。扫描不到、进程权限拒绝或用途不明即保留并列具体待核项，不以此阻断无关清理。
