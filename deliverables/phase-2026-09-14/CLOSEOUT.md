# 原定9/14阶段：9/13提前验收收尾

实际验收2026-09-13，依用户“现在就做明天的验收”执行；判定见[阶段报告](README.md)。固定输入a91b470；原9/10与原9/16目录历史快照未改。限定进展通过，正式M1/H2/H3/二维定位和音频/整机仍未通过。

## 批准身份与归位

| 原任务包及批准版本 | 当前唯一运行/证据入口 | 本阶段集成决定 |
| --- | --- | --- |
| A current_build / d0ce1c2 | task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/current_build | 保留安全构建/PS合同入口与B批准，不另建采集工程 |
| A FFT29扩展 / b8c5e87 | task-packages/PKG-A-ACQ/tasks/fft29-bitexact-budget-01/coverage-extension-01 | 只获归档覆盖批准，不替换活动算法或把研究TB挂入整机回归 |
| A C板实录 / df4b756 | task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913 | 冻结原BIN/CSV/WAV和几何，不迁RTL、不重复复制录音 |
| B reference25实录诊断 / e5b6753 | task-packages/PKG-B-ALG/tasks/c-board-algorithm-01 | 保留可运行诊断包；A只批准离线诊断，正式DOA/DAS及数制/调度待H3，不新复制model生产源 |
| C双轴 / 407849e | task-packages/PKG-A-ACQ/outsourcing/motor_control_plan及motor-407849e复核 | 条件预算/原则研究，不接RTL/PS/BD/XDC，不派采购或硬件动作 |
| 既有C001～003库 | rtl/common、rtl/acquisition、tb对应文件与sim/modules.json | 已在活动目录；本轮原字节/仅检出换行及前后哈希核对，无新增修改，不将旧6组回归写成本轮新运行 |

**本阶段无新增获准接入生产主链的源码。** 新批准的B源码属于限定诊断，例外原因已逐项列明；不是只交README，也不为填满活动目录复制未准入定位/波束模块。H3后由A/B一次约定文件归属再做正式算法接入及新位置回归。

## 可复现检查与集中材料

仓库根目录执行，Python3.12+NumPy；输出必须全新，不覆盖本目录冻结证据：

```powershell
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B deliverables/phase-2026-09-14/check_stage.py --out 'C:/temp/ss-stage-review-new'
```

本轮实际输出evidence/check-2026-09-13-02：293项固定Git索引、B10项测试/31项文件依赖、A两段各32000组及40项哈希、FFT196帧覆盖1673216码复查通过。命令、时间、退出码及原始日志集中在该目录；没有新Vivado/C模型整链/板测。原始大文件不重复打ZIP，依manifest的commit/path/Git blob/SHA256从Git导出，相关任务包仍保持原字节与唯一入口。

待完成技术项按README及B原H3-GAPS执行，不因阶段收尾而虚假关闭。若9/18缺真值/完整算法，按实际范围评审，不改动本次冻结记录。

## 本地材料与发布

开始核对最新远端a91b470，实际共享main已由上一批发布同步到同SHA；本次没有另建Git工作树/分支，没有夹带9项PYNQ未审工作。前一轮已清理C盘pub/fft29-coverage-publication/c-adapter-publication，本轮核查工作树清单，未再建同类副本；其他恢复备份和外部运行目录保留，不扩大清理范围。

仅发布本阶段记录/核查脚本/新日志/索引和当前入口更新。最终暂存前核对忽略日志、源码原件哈希、文档链接；推送后核对实际共享main、origin/main、直接远端及本批未提交材料。最终提交号与核对结果由完成回报提供，不在提交内循环记录自身SHA。B/C其他机器不能代签同步。

发布准备实际检查：117个本地文档链接可达，本阶段目录无被忽略而漏交的文件；旧作者清单/旧阶段快照未修改。链接检查首轮因根目录README的父路径为空而报错，未采信其汇总；改用解析后的绝对父目录后重新检查通过。未审PYNQ变更不在发布允许清单内。

## 发布后批次核对（2026-09-13）

| 项目 | 实际结果 |
| --- | --- |
| 主体发布 | 11395e9908a52b2ec615b2f1062f9fb4166c7886，24条文件变更，已非强制推送main；本表为随后仅补回执提交 |
| 本机与远端 | 实际共享main、origin/main、直接远端均为11395e9，领先/落后0/0；最终回执提交后再核对并向用户报告SHA |
| 本批材料 | 新阶段目录未跟踪0、忽略0；新日志、失败说明、索引、脚本均正常跟踪。活动RTL/TB/sim、两份A交付、B算法包及9/10和原9/16历史快照相对输入a91b470改动0 |
| 在做工作 | 9项PYNQ未审修改/新增保留，不夹带；发布后发现远端新增dual-axis-shopping-list分支，属本次固定范围外后续工作，未合入或清理，不影响本次已固定阶段结论 |
| 清理 | 本轮没有新建复核/发布工作树，无新增重复工程需要删除；此前3个C盘发布工作树已经清除，当前主仓登记仅共享main。外部原始运行/恢复备份及长期分支保留 |
| 完成边界 | 本阶段限定进展验收及本机收尾完成，不代表M1/H3/整机或B/C设备同步完成。无新增已准入生产源码；诊断/研究入口及后续责任见上文 |
