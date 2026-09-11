# 输入获取失败记录（2026-09-11，事后整理）

以下为当前任务工具输出摘录，不冒充完整网络原始日志。没有改写 B 证据。

- 共享仓库全量 fetch 长时间无进展，取消；窄范围 fetch 曾出现 Schannel SSL 握手失败，随后仍无进展。未切换共享工作区。
- 改用独立 shallow/blobless clone，成功取得指定 B HEAD；Windows 部分克隆的 lazy checkout 多次出现 `unable to read sha1 file`。未使用检出失败的文件作为输入；中止后可能留下 index.lock，未删除。
- 固定 SHA 的匿名 raw 下载返回 HTTP 404，未将响应当源码。
- 对单个已知 Git blob 显式 fetch 成功；批量普通 fetch 再次失败：

```text
fetch 1..12: 1
fatal: bad revision '4bb40e8b960d7cf45781324a3c504e581a3f99c0'
error: https://github.com/TophBeifong1744/Competition_fpga.git did not send all necessary objects
```

- 给显式对象 fetch 加 `--refetch --no-filter` 后单对象重取退出码 0；最终输入以 Git blob SHA-1、B manifest SHA-256 及 frames 中的 NPZ SHA-256 联合校验，不依赖故障中的工作树/index。
- 首次 12 对象批量 `--refetch --no-filter`：第一批退出码 0，第二批 120 秒后 `subprocess.TimeoutExpired`。改为跳过本地已有对象、逐对象获取；单独获取第二批首对象 `fafbc1d62dda42e8f88eee267ed3736f14c55d1b` 退出码 0（约 6.7 秒）。后续失败自动保存到 `reference/fetch-failed-*.json`。
