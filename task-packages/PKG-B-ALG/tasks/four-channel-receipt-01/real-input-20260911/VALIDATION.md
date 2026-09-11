# 本次登记验证

2026-09-11，工作区 `F:/NUEC/review-worktrees/member-b-real-input-register-01`，分支 `task/member-b-real-input-register-01`，基线 `e811c399adaa083d520bfda998f15fe86b445b9a`。

远端获取：最初 schannel 返回 SEC_E_NO_CREDENTIALS；改用命令级 OpenSSL 后 fetch 成功，未改全局配置。main 为 e811c39，实录分支为 2e2f685；祖先检查表明原交付未包含于 main。

```powershell
git -c safe.directory=F:/NUEC/review-worktrees/member-b-0910-closeout -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 fetch origin
& 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B task-packages/PKG-B-ALG/tasks/four-channel-receipt-01/real-input-20260911/verify_register.py
```

登记验证退出码 0，输出：

```text
PASS: 10 historical evidence hashes; 76 original Git blobs; 76 unchanged receipt-update blobs; receipt identity; capture index; replay syntax
No numerical diagnosis or 64-test historical regression rerun; no hardware acceptance.
```

另外实际核对：本机 B-REVIEW 与 2e2f685 的远端原件在统一 CRLF/LF 后相同；登记的回执 SHA-256 取 Git blob 原字节。历史证据按原字节复制，以本目录 .gitattributes 禁止换行转换。可选 replay 脚本的 snapshot 检查至数值计算/结果生成部分与原脚本逐字一致，仅输入路径、发布文件身份读取及输出落点改变；未重新运行数值诊断。其 `--help` 可运行。

适用检查包括本次范围 diff、文档相对链接与暂存历史文件哈希检查、`git diff --check`。未运行历史 64 项回归、综合、实现、时序、BD 或板测。历史 64 项通过只来自原 B 回执和 historical-evidence 的对应日志；新增材料仍属作者自检，待 A 复核。
