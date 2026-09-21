# H3 E01/E02 增量 Spec 复核

准确 SHA：a7f70c5149a6503effdbbf16a9903d42c2d39e6d；基线 0abdc91c57787b7c868a797b88f35129de169faf。先读 PUBLICATION-REPAIR-20260921.md，再读 repair-h3-e01-e03/README.md；以原 B 反馈及 ROUTE.md:15、23、25 为依据。

本轴未发现新增阻断，E01/E02 在限定 Python 顺序状态模型内已修复。results.py:45-46、102-103 独立保存 ever_committed；barrier:49-60 只改变可用性，finish:79-87 用历史提交位和 epoch 区分当前追溯故障与旧会话回调。CLIP/DROP/STOP/RESET 后当前 epoch 晚错均 fail-stop；显式 start 后旧 epoch 回调保留审计，不撤销新会话。stop 同次 error 也不吞掉晚错。

results.py:5-13 递归生成带类型的不可变快照，:41-46 绑定首次成功 submit 的会话配置。独立检查嵌套 dict/list/tuple/bytes 别名修改、字典顺序、bool/int 和 list/tuple 等类型差异、跨 interval 配置变更及新 session 放行。原 E02 可变引用和同会话换配置不再误放行。

实际命令：`python -B F:/NUEC/review-evidence/h3-repair-a7f70c5/spec/probe.py`；20 项独立边界检查全部通过，源码哈希、逐项输入和结果见 results.json。没有修改原包。E03 prepare/官方回归由主复核单独报告。本结论不覆盖直接篡改模型内部 entries，不代表真实并发、生产 ABI、C 候选、ARM、RTL、CDC 或实板批准。
