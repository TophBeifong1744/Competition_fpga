# 三次冷启动结果：用户回传

记录日期：2026-09-08。来源为本工作聊天，不是助手串口采集。

用户先粘贴下列完整输出，随后在“完成三次冷启动”的任务上下文中确认：“三次都是上面的输出，源码在……，其他的你自己去文件夹里面找，然后帮我写入 PKG-A-ACQ，确认完成任务后推送”。按用户确认记录三轮结果一致；每轮精确时间、独立串口原文件和当时加载 ELF 哈希未提供。本轮未在 ddr_test 下检索到含最终 PASS 的 txt/log/csv 原始日志。不以复制文本构造三份独立证据。

| 轮次 | 冷启动与结果来源 | 完成/通过模式 | 错误 |
|---|---|---|---|
| 1 | 用户确认 | 5/5 | 0 |
| 2 | 用户确认同一输出 | 5/5 | 0 |
| 3 | 用户确认同一输出 | 5/5 | 0 |

## 用户粘贴的共同输出

下文仅去掉聊天中标题前的转义反斜杠，数字与内容保持；不是原始串口字节流。

```text
=== DDR five-pattern test v1 ===
Start=0x01000000, end-exclusive=0x01100000
Bytes=1048576, words per mode=262144
Program end=0x001119C0
Data cache disabled; destructive test begins.

[1/5] ZERO: writing...
ZERO: checking...
ZERO PASS: checked=262144 words, errors=0

[2/5] ONES: writing...
ONES: checking...
ONES PASS: checked=262144 words, errors=0

[3/5] AA: writing...
AA: checking...
AA PASS: checked=262144 words, errors=0

[4/5] 55: writing...
55: checking...
55 PASS: checked=262144 words, errors=0

[5/5] ADDRESS: writing...
ADDRESS: checking...
ADDRESS PASS: checked=262144 words, errors=0

=== SUMMARY ===
Completed=5/5, passed=5, errors=0
DDR TEST PASS
```

当前文件夹中的 ELF 已单独归档和计算哈希；不能因此倒推出三次运行时均已记录该哈希。是否需要原始逐轮日志由 B 在完整包复核时判断，作者不代签。
