# B 阻断反馈发布

本分支仅发布 B 对 `bbe39c38dc36ccb4c0492f492b86f6c46d885fbe` 的复核证据，结论为需修改。没有合并 A 候选或 main，也不修改 A 工程入口。

先读 A-FEEDBACK.md，再读 B-REVIEW.md。B-EVIDENCE-SHA256.json 覆盖原始 B 证据44项，不覆盖自身、本发布说明和本目录 .gitattributes；后两项由本发布 Git 提交绑定。B 的无效 ELF 文件只供解析器负例，禁止作为板卡加载固件。

反馈分支基于已发布父提交8371f01，因此不包含 A 的新入口源码。A 应固定候选bbe39c3，在包外取得本反馈目录，再使用自己的新工作区修复；不要将整个反馈分支覆盖到实际工程或作者冻结目录。

日志里的 F:/NUEC 路径是 B 原执行路径，保留原字节。`negative_contract_checks.py` 可传入本机候选包目录及不存在的新输出目录。Tcl补充/竞态脚本保留原 B 路径；异机复跑时在独立副本调整 PACKAGE/TCL/输出路径，记录实际改动，不覆盖已归档结果。`audit_archive.py` 的Git和Capstone路径也需按本机安装调整。不得把路径调整、模拟硬件或模拟完整gate前提称为真实AMD编译/板测。

`spec/reproduce.py` 为未执行完的草稿，不计入证据；真实已完成的最小负例和范围见B-REVIEW。修复请用新的准确SHA交回B，不改旧清单来让原SHA看起来通过。
