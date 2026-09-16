# 准备阶段限制及失败记录

- 2026-09-16，用户明确选择复用现有 continuous_platform / four_mic_continuous。工程未创建副本或后台修改。
- git ls-remote origin refs/heads/main：Schannel报 `AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS (0x8009030e)`；单次 `-c http.sslBackend=openssl` 再查，退出128、没有获取main SHA。未改Git配置，未fetch/reset/checkout。准确批准和合并Git对象已存在且祖先检查退出0。
- 新单测初次15项有1项失败，原因是fixture返回长路径而预期仍是TOPHBE~1短路径；原日志entry-tests-01.log保留。仅测试期望增加resolve，之后补充子例，最终18项通过。
- Python内置Tcl最初初始化失败：`_tkinter.TclError: Can't find a usable init.tcl`，查找目录为Python运行时的tcl/tcl8.6；不代表加载脚本失败。没有安装或修改环境，找到现有 `F:/AMD/2025.2/tps/win64/git-2.50.0/mingw64/bin/tclsh86.exe`，用它实际执行纯mock的test_load.tcl，四项通过。
- 准备过程没有应用编译或ARM固件新链接；gcc只调用--version，objdump仅反汇编已有ELF。现有ELF哈希仍ebc576e2…；这些结果不可计为本轮新构建。
- 新CMake hook尚待用户实际接入/构建。stage=pre对当前未接入工程的拒绝是预期负例，并已保留request/failure与退出码。
