# A：四路跟踪与三路诊断音频复核清单

仓库：`TophBeifong1744/Competition_fpga`。分支：`task/member-b-four-track-01`。复核时须固定 **B 发布回报中的准确远端 SHA**，不能只按浮动分支名批准。本清单本身不声明已经推送。

实现版本：四路候选跟踪 `e93169d526e9e94a98947c86d2c92bcab3c46a2e`；三路音频 `5d905b29c4f77c63b4d4a205b6a74a6ed7a48a91`。之后本轮只补 B 试听、交付说明与校验；最终提交仍须核实差异。若远端仍是 e93169d，说明新增音频尚未发布，不按旧版本复核本批。

## 申请范围

申请四路真实录音的离线候选跟踪、单麦／手动／诊断自动音频、生命周期与逐码复现材料的限定入库。B 新实现不自审自合。默认 PHAT、原 Tracker、reference25、A/C 原件及旧复核记录未修改。

目标位置保持 `task-packages/PKG-B-ALG/tasks/four-channel-track-01/` 及其 `audio-01/`，暂不替换活动生产算法。目标存在门仍缺，`direction_accepted=false`。不申请精度／错向率／降噪收益、完整 H2/H3、实板、实时或完整定点格式冻结。

## 建议复核

1. 从 `audio-01/README.md` 和 `verify_package.py` 进入。检查父包原 28 个文件、输入依赖及本轮新目录清单，保留旧父包清单；不要把目录增量误当录音被重写。
2. 复跑音频包入口：50 项测试、12 WAV、383,808 个码值的另一路重算、时间裁剪、未知／过期方向权重。确认 golden 是作者测试证据，再给出 A 的独立判断。
3. 检查帧末可用时钟、同参考行 [8,31992)、统一增益 32、音频可用延迟假设 8 样点。不能因预计算波束缓存而把未来方向用于早先样点，不能把离线索引合同当实时测量。
4. 重点复测 HOLD 临期换方向／释放的两项回归：原日志权重跳变 0.25，修复前源码与原 SHA 绑定；修复后测试通过。短实录本身没有触发该边界，不能用 WAV 未变代替边界验证。
5. 复核父包候选的限制：center 61 帧中 LOCKED 21、HOLD 18；quiet 没锁定，但 35 帧数值一致候选在允许范围之外。不能将此说成目标存在门完成或定位正确。
6. B 已回报三路“无差别、无发闷、失真、断音、爆音或音量突变”，三个试听 WAV 与提交 5d905b2 绑定。设备、音量保持情况等未确认；无客观收益结论。旧运行字段保留生成时状态，当前反馈读 `evidence/listening-01.json`。
7. 分开说明输入／源码哈希、算法与 WAV 数值复现、生成 JSON 的字节差异。跨 CPU 尚未由 B 复测，复核时不得仅看最终计数。

## 命令

Python 3.12、NumPy 2.3.5；从独立、干净的准确提交检出根目录执行。复跑目录必须未存在。

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/verify_package.py
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/reproduce.py --out ..\review-evidence\four-track-audio-a-review01
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/verify_package.py --compare-saved
```

若父包跟踪增量 e93169d 尚未独立复核，可同一次复核中运行以下既有入口，不重跑六麦历史研究：

```powershell
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/reproduce.py --out ..\review-evidence\four-track-a-review01
python -B task-packages/PKG-B-ALG/tasks/four-channel-track-01/verify.py --compare ..\review-evidence\four-track-a-review01\replay
```

通过后由 A 按准确 SHA 与限定范围合入，不夹带其后的未审提交。任务分支只有确认本批已完整入库、不再承载继续工作后才能清理；本轮没有新增工作树。B 本地的未发布／独有材料需由 B 核实，A 不代签本地已清理。
