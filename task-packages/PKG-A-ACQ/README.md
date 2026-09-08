# PKG-A-ACQ · 工程与采集/导出包

负责人：A 拓芙。技术复核与合入：B BryanZheng802。完整包状态：进行中。

本包已包含 H1 候选与 DDR 五模式自检交付，不代表完整采集包已验收或 H2/H3 通过。现有 one 工程不重复创建。

## DDR 自检交付（2026-09-08）

[DDR 证据入口](evidence/ddr-five-pattern-v1/README.md)：源码、链接脚本、构建描述、当前 ELF/XSA/bit/初始化文件、ELF 检查和用户回传三轮结果。用户确认五模式三次通过，作者侧源码/ELF 检查完成，B 复核待进行。逐轮原始串口文件未提供，不伪造；不扩大为完整 DDR、PYNQ 或采集验收。

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

A 后续回传 B 已按 ss-data-draft-0.3 完成读取器、错误检查和连续区间识别，47 项测试通过，覆盖所列 15 项；这是用户转述，作者侧未独立查看 B 源码与测试日志。后续导出沿用 0.3；共同版本确认与完整包审批分别记录，不能由该消息推定 DDR 或完整包已获 B 批准。旧 hsc119 技术复核安排不再适用。
