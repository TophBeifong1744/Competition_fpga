# H1 交给 B：确认接口并开发读取器

接收人：BryanZheng802。当前候选 ss-data-draft-0.3，属于完整 PKG-A-ACQ 的中间交接，不是完整采集包验收。

1. 阅读 payload/docs/minimal-data-interface.md，确认或集中提出一次接口修改意见；A/B 的确认须绑定 evidence/h1-files.json 的 SHA-256。当前未代签任何一方。
2. 使用 payload/examples/h1 中两个样例试接输入，在自己的 PKG-B-ALG 内实现读取器、异常检查和连续区间识别，不必等待硬件或完整 M0。
3. 按 reader-test-plan.json 执行 15 个测试预期，保留实际结果；本包的 check_h1_fixtures.py 仅为样例自检，不是你的读取器测试成绩。
4. H1 共同约定可以先完成，不以读取器全部实现为前提。没有声学录音时不报告真实 DOA 或音频收益；H2/H3 尚未完成。

版本清单 SHA-256：ef09838face445cc4f2a87d56245ad64574fa3e9f4d12032e4b0723a7f1eca96。

本分支按既定规则从 codex/toph-development 建立；该集成分支当前落后于 main 的新分工文档。请以 main 中 2026-09-08 的 H1/H2/H3 与 A/B 交叉技术复核安排为准，勿从旧基线推断 hsc119 仍承担技术审批。发布仅增加本任务包，不夹带其他提交或更新总工程。

正式合入须 B 批准准确版本并负责执行；当前只有上传交接，未合并，也未声称 B 已收到或确认。
