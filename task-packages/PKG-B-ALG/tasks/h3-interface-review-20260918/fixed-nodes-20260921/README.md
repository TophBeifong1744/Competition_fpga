# B 固定数值节点集中交付

实际日期 2026-09-21；作者自测完成，待 A 独立复核，未合入 main。
依赖 b5913e596e28b30f9e04cf2c9ba365430b8914df；该依赖尚不在已刷新 origin/main e55f0d520b654380d0cacd642f2fb45cad767640 中。独立任务分支 task/member-b-fixed-nodes-01 不改原审核分支。

## 范围与结果

三份工作材料以原字节归档，原 README 的暂存路径、后续步骤及未提交表述属于当时记录；本页为新交付入口。每组 WORK-SHA256.json 保留，旧父快照另存 SNAPSHOT-before-nodes.json。没有修改默认算法、阈值、录音或 A/C 文件。

| 组 | 本轮已验证 | 仍未完成 |
| --- | --- | --- |
| [B1/B3](b1b3/README.md) | 13 组前端、7 组功率、4096 条状态序列；严格输入候选拒绝原入口的 7 类非法值 | 完整 FFT 动态范围、生产入口接入 |
| [B2/B4](b2b4/README.md) | 33 个适配值、32 个蝶形节点、256 项倒数表、207 个归一化输入、补谱和错误汇总反例 | 全域误差界、AMD 逐码、真实异步完成协议 |
| [B5/B6](b5b6/README.md) | 56 个 lag 用例、656 个 DOA 时延盒顶点、16 组固定延迟跨块 PCM 对照 | 动态切向/HOLD/TTL、多 bank、生产 delay ROM、全中间字宽 |

必须反馈 A：拒绝前 xy 可达 ±2,531,477；8 个顶点超出 S22，原宽整数模型将它们拒绝。固定几何和合法 pair 时延域下，拒绝前至少 S23F20，不能先截成 S22 再拒绝。旧数制表不覆写，以此作为显式修订建议。

固定延迟 StreamDAS 16 组最终 PCM 精确一致；直接逐块调用旧单块函数在数学夹具上累计差 159 点，不代表实录断音。新候选最多需 9 样点 lookahead，未证明满足旧 8 样点合同。小向量 CORDIC 误差缺口仍保留；现有范数门排除该测试数量级。

## 复现

在仓库根目录，CPython 3.12.14、NumPy 2.3.5。依赖可在独立 venv 中安装 `python -m pip install numpy==2.3.5`，不修改全局 Git 配置。包内 `* -text` 保留原字节；冻结文件失配时按脚本给出的路径及期望/实际哈希定位，不重写哈希。

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/fixed-nodes-20260921/run_all.py --repo . --out ../b-fixed-nodes-review-new
```

输出目录必须不存在。从归档位置实际复跑三组退出码均为 0，完整结果/命令/日志在 validation/portable01。只做本批节点运算，没有全 FFT/IFFT 或旧研究重跑。整数、状态及历史材料哈希严格检查；浮点派生文件不得仅凭计数或 JSON 字节差异裁定算法复现。

新增输入校验、FrameGuard 和 StreamDAS 均是独立候选，未接入原链。未运行 RTL、AMD IP、实板或整链实时测试；WCET、总缓存/带宽和资源仍不能据此填成通过。下一步是 A 复核本增量及 S23/9 样点接口影响，再推进动态 DAS 与完整预算，完整 H3 未关闭。
