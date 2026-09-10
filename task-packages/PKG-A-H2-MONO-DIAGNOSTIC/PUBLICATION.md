# 2026-09-10 待审发布说明

分支 codex/toph/mono-diagnostic-delivery，从 main 9878ccafdda6cd5a522cc9de95c1277bcee70f08 建立。用户授权上传 DDR、单麦等已完成材料；本次不合入 main，不批准完整 H2。

## 上传范围

- 原始 42 文件单麦包完整保留：两段各 48000 样本的 CSV/metadata、原始 BIN/WAV、工程快照、读取与校验源码。原 README 的“未推送”“未绑定 Git”等是打包时历史状态，不改写原件或原清单。
- publication/mono_closeout_20260910：工程任务离线补证与有限裁定快照，含实现报告、初始化/BSP及低频分析。
- publication/mono-review-20260910：A 独立原始数据复算脚本、结果及中间复核。历史脚本含原电脑路径，仅供审计，跨机运行使用下述入口。
- H1 A 确认增量见 task-packages/PKG-A-ACQ/REVIEW.md，不修改冻结 H1 payload/清单。

## B 验证入口

Python 3.10+，从本包根目录运行：

```text
python -B source/file_manifest.py verify
python -B source/mono_delivery.py verify
python -B source/test_delivery.py
```

原 SHA256.json 覆盖原包 41 文件，不含清单自身、本说明、publication/ 和 .gitattributes。新增文件由本次 Git 提交固定，工程收尾另有原清单。冻结文件禁止 Git 换行转换。B 须自行复核，不把 A 自检当成 B 的批准。

## DDR 已有远端交付（不重复复制）

- codex/toph/pkg-a-acq：9c3301e2a8564d454fa9a3d2b034334f18fbe055，DDR 五模式与三轮用户报告证据；保留原日志和加载身份限制。
- codex/toph/ddr-dma-delivery：4bfaeb36977ea61201b6b78803351cdb9cc9d239，任务一接口测试/源码与任务二、三 DDR/DMA 数据交付。
- 本次直接核对上述远端 SHA。远端存在不等于已批准或合入 main；B 可分别获取分支。

## 限制

单麦仅 diagnostic，独立 ss-mono-diagnostic-0.2，不能当四路 H1 或送六麦定位。用户试听清楚、无明显嗡声/断续/失真，但未指定具体 WAV/增益，不是客观音质指标。供电、外部 IO 时序、加载身份仍待验证；新增低频/实现补证不冒称 A 已独立复现。工程原记录的暂停板测属于当时状态，后续安排按新任务执行，本次上传不改变技术验收结论。
