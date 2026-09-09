# PR #3 修订交付入口

本次处理 A 对 `25a6257fe3136b058cefa06e86fde0f3c8dd8dff` 的请求修改。
逐项整改、实际复现结果及限制见 [整改说明](revisions/pr3-repro-01/README.md)。

本轮支持的验收入口（在本包根目录；Python 环境要求见整改说明）：

```powershell
python -B revisions/pr3-repro-01/verify_release.py
python -B revisions/pr3-repro-01/run_all.py --out <新的输出目录>
```

六个 `research/*-01` 目录保留为不可变的历史交付，唯一补充是找回的原始 `stable-wrong-01/run.log`。
旧 `audit.py`、`final_check.py` 和 `analyze_stable.py` 保留以追溯原版本；本次审阅使用上面的修订入口，不能只调用旧入口或读取旧 `audit.json` 的 PASS。

新增入口读取原始算法、协议和证据，使用独立历史评审快照解析冻结引用，不覆盖当前 `REVIEW.md`，也不修改默认 PHAT、跟踪器或其他成员成果。
本轮仅申请六麦合成离线研究材料入库，等待 A 再复核；不申请算法替换、四麦主线、实板、H2/H3 或完整算法包验收。
