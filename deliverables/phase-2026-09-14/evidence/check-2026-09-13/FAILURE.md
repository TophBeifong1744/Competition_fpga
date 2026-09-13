# 阶段索引首轮停止

2026-09-13。check_stage.py在运行任何测试前遇到rtl/README.md工作树CRLF与Git LF差异，报Fixed input differs并退出1；没有生成通过记录或修改原件。

这是本轮新索引脚本未区分活动目录检出换行的错误，不是被验收源码失败。修正仅允许existing-active-module-library组的CRLF/LF等价，分别保存固定Git字节哈希和实际工作树哈希；其余冻结证据仍要求原始字节一致。下一次使用check-2026-09-13-02新目录，不覆盖本次记录。
