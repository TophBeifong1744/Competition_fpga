# PKG-A-ACQ · 工程与采集/导出包

负责人：A 拓芙。技术复核与合入：B BryanZheng802。完整包状态：进行中。

本次只完成 H1 的可执行候选资料，不代表完整采集包待验收、H1 双方确认或 H2/H3 通过。现有 one 工程不重复创建；UART/DDR 板测另行继续。

## H1 入口

- [接口候选](payload/docs/minimal-data-interface.md)：ss-data-draft-0.3。
- [固定码型](payload/examples/h1/code-pattern/metadata.json) 与 [CSV](payload/examples/h1/code-pattern/samples.csv)。
- [重启片段](payload/examples/h1/restart/metadata.json) 与 [CSV](payload/examples/h1/restart/samples.csv)。
- [读取器测试预期](payload/examples/h1/reader-test-plan.json)：B 实现读取器时消费；不是已运行测试的成绩单。
- [样例自检](payload/scripts/check_h1_fixtures.py)：只核验这两个样例，不替代 B 的读取器或公共 TB。
- [确认记录](REVIEW.md)、[清单](manifest.md)。

在本包 payload 目录运行 `python scripts/check_h1_fixtures.py`，只需 Python 标准库。预期输出固定码型和重启样例检查通过；不会写文件或连接板卡。

## A/B 交接

A 负责按约定导出；B 负责读取器及完整正/负例测试。双方一次确认格式、编号/错误语义及暂定参数即可开始，不必等全套 M0、接板或一小时长稳。

A 的本次请求是准备 H1，不视为已批准生成后才出现的 0.3 版。当前 A/B 均无针对该版本的明确确认。双方可继续包内开发；正式合入仍须 B 批准准确版本并负责执行。旧 hsc119 复核安排不再适用。
