# 2026-09-18 阶段收尾

## 2026-09-20 run05 限定补验发布

B报告 `7b25d51` 批准 `7a17edd` 的run05软件断流闭环，报告原件位于 `docs/reviews/h3-run05-7a17edd/B-REVIEW.md`，8993字节、Git blob `6d5e16b24be041da01f48c4383a99430025c034c`、SHA256 `1ea8bc856c54619bd703686c5c4da2f0cd12456fb94011a9406ac5a1cda6cf88`。任务包原Git对象入库，不迁移为默认算法或生产RTL。用户授权保留main正式阶段记录并更新状态，解决其与候选草稿的唯一冲突。

发布前独立工作树最小检查：包清单68项PASS；上游18项Git输入PASS（2项允许的CRLF规范化）；run05冻结14数组/状态/事件全部精确一致；39项单测PASS。未重复B完整复核、三路音频50项检查、Vivado或板测。使用包内既有脚本，Python为Codex缓存运行时：

```powershell
$pkg='task-packages/PKG-B-ALG/tasks/h3-complete-20260918'
python -B "$pkg/source/seal_package.py" --package $pkg --verify
python -B "$pkg/source/seal_inputs.py" --repo . --out "$pkg/inputs.json" --verify
python -B "$pkg/source/check_golden.py" --repo . --golden "$pkg/evidence/run05/golden/golden-stages.npz" --out ../h3-run05-publication-smoke-20260920.json
python -B -m unittest discover -s "$pkg/tests" -v
```

输出必须使用未存在的新文件；本次检查JSON保存在独立发布目录旁，不覆盖作者证据。合并提交后再次核对包对象身份并运行冻结检查。最终远端身份与共享main同步结果见发布回报；不代签B设备同步。其他采集、分帧和Skill待审材料保留，不夹带、不删除工作树。以下为9/18历史收尾，不将“尚待复核”当作run05当前状态。

- 实际验收：2026-09-18 晚间；基线 `bff9369a5c7f166344c02095df61e91e1c2f4681`，输入和逐项结论见 [README](README.md)。声学/完整 H3 **未通过**，阶段收尾是记录结论，不是批准作者候选。
- 本阶段**无新增获准源码**可从任务包迁入 `model/`、`rtl/`、`tb/`、`sim/` 或 `ps/`；原任务包→活动文件映射为“无”。此前 `f364a02` 的限定诊断材料和 `b1d51d4` 的舵机模块集成保持原批准范围，不在本阶段重复搬迁或重签。
- 新 H3 包 `7a17edd` 与新录音 `8f708e4` 留在各自待审分支；原因分别是缺 B 对最新候选的独立复核及录音质量/真值不足。A 新帧适配和两项 Skill 9/23 候选同属未完成/待审材料，不随本次文档发布夹带。责任与下一步见 README。
- 本次实际检查：刷新远端；核对 `main`、`origin/main` 与候选准确 SHA；阅读 9/18 日历、既有 B/A 限定复核、A 候选一页入口、run05 的 39 项作者测试日志及 14 数组冻结检查、录音/Skill 范围说明、C 当前评审。`git merge --ff-only origin/main` 已使本地 main 从 `5cfa02e` 到 `bff9369`，无 tracked 冲突。未重新运行 H3 作者脚本、综合实现、时序或板测；不能写成独立测试 PASS。
- 共享目录现存多项未跟踪工作树/任务资料（包括 `continuous-work*`、采集/帧适配、Skill 候选）；它们不是本阶段已批准材料。没有删除、覆盖、打包进主线或用忽略规则隐藏，待各自责任人按准确包复核后处理。本轮只提交本目录和当前状态/计划指针；发布后再核对本地、跟踪与直接远端 main 及本批遗漏材料。
- 旧阶段快照不修改；今晚的失败和待测项不得回填为 9/14 或 9/16 通过。新独立复核若于本记录后产生，以真实日期另记补充记录，不重写本次原始裁决。
- 发布 SHA 由提交历史及最终发布回报确定；本文不预填未发生的提交/远端状态。
