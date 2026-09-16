# 交回 A：timerfixed-entry-01 需修改

B复核 `bbe39c38dc36ccb4c0492f492b86f6c46d885fbe`，结论：**需修改，未合并**。

三项要求：

1. **TF-B-01 / P1**：`check_entry.py:103-108`未验证ELF启动入口。仅将真实归档ELF的e_entry改为RX起点0x01000000或0，原verify_elf仍接受。请绑定实际链接配置和合法启动入口，并回归无效入口拒绝。
2. **TF-B-02 / P2**：`check_entry.py:140-145`整条命令casefold，使`-DSDT`/`-Dsdt`、`-U__clang__`/`-u__clang__`被认为相同。请只规范化路径，保留编译选项和宏/值的语义。
3. **TF-B-03 / P1**：`load_timerfixed.tcl:8-25`检查后仍按活动路径下载。在等待时换ELF，mock dow会读到替换内容并con，包括旧错计时ELF。请加载与检查/构建收据绑定的受保护产物集合，并处理并发写入；不是要求GUI不可绕过。

归档检查通过：88文件/87清单、父包未变、26快照、32准备清单映射、新对象/ELF合同与计时、27字节差异说明均已独立确认。18+10+34单测、作者4项Tcl及B补充7组均通过，但没有覆盖上述缺陷。

反例全部离线，无板卡、无真实构建。见 `negative_contract_checks.py`、`negative-run01/result.json`、`standards/reproduce_artifact_race.py`、`standards/artifact-race-results.json`。已有输出勿覆盖；复跑使用新目录。`spec/reproduce.py`未完成，不计为执行证据。

请保留冻结原件和失败历史，在新SHA修复并交回复核。没有要求重复上板、长稳或增加阶段门槛。完整说明与实际命令见 `B-REVIEW.md`。
