# Git 打包记录

2026-09-11 首次按清单暂存时，Windows Git 对独立工作区中的深层参考路径报 `Filename too long`，`git add` 返回 128；未提交、未修改任何研究数据。后续给当前命令显式加 `-c core.longpaths=true`，不修改全局 Git 设置、不移动或压短 B 原始来源路径。

报错对象：`reference/b-dynamic-range/dependencies/task-packages/PKG-B-ALG/payload/model/python/six_mic_baseline_core.py`。

加入此记录后生成最终清单；上一份清单保留为 `SHA256SUMS-before-packaging.json`，不再作为最终校验入口。最终入口仍为任务包根目录 `SHA256SUMS.json`。
