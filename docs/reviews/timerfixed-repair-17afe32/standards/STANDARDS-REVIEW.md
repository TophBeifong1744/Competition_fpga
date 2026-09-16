# 规范／加载保护轴：17afe32cebcff742bb2f9486388e91d9403f83dd

结论：本轴未发现新增阻断，TF-B-03在当前限定Windows本地NTFS、正常进程存活及全部硬件mock范围内通过。整体候选结论由主审汇总其他轴；此结论不代表真实XSDB下载兼容性或板测通过。

## 代码与规范核对

- `guarded_load.py:19-26`在活动三产物、对象及源码/配置证明锁内运行检查，随后封存；`artifact_guard.py:84-88`在封存句柄锁已取得后重算哈希，封存前的复制窗口没有直接放行路径。
- `guarded_load.py:18-39`将封存锁保留到会话退出；`load_timerfixed.tcl:43-54`使用会话回传的封存路径执行fpga/source/dow/con，`:56-60`在正常及异常路径请求释放并等待keeper退出。默认dry及检查失败前不操作硬件保持。
- 以上符合repair-01/README.md:17-21限定合同。AGENTS.md和CONTRIBUTING.md要求区分模拟、实板及独立复核，本轮没有扩张这些声明。
- 无额外硬规范违规或值得单列的维护气味。原路径常量双份维护问题已由封存路径传递消除。

## 独立补充实测

未重复作者82项全套，补测以下七组：

1. 已关闭原文件句柄但保留可写mmap时，获取保护锁拒绝，WinError32。
2. 硬链接别名不能写受锁文件；退出后可写。
3. 第二文件加锁失败时，先取得的锁正确释放。
4. 真实keeper正常RELEASE。
5. 真实keeper stdin EOF，拒绝并释放。
6. 真实keeper未知命令，拒绝并释放。
7. 原生Tcl在con处注入失败：三封存文件到con内仍不可写，finally后全部可重新以写模式打开。

第4-6组同时验证：gate执行时七种活动产物/证明文件写入、活动app目录更名均拒绝；READY后封存三文件各自写入/替换/删除以及三级祖先目录更名均拒绝；此时活动app整目录可以更名，封存哈希保持不变。

使用指定Python及F:/STUDY/IT/Anaconda3/Library/bin/tclsh.exe；全部fixture明确位于本包外F盘证据目录，不使用C盘TEMP。均在默认工具权限运行。keeper/NTFS锁/归档ELF及Tcl真实执行，其余完整Vitis gate前提模拟；硬件全部mock，无实际A工程或XSDB访问。

## 证据与限制

独立结果：`independent-guard-results.json`、`independent-keeper-results.json`、`con-failure.json`。重现源码：`independent_guard_checks.py`、`independent_keeper_checks.py`、`keeper_probe.py`。会话内活动锁探针保存于各fixture records/guard子目录的active-lock-probes.json。程序有意保留fixture及日志，重跑应使用新的包外输出目录。

真实XSDB读共享模式、现场完整gate、管理员或进程被杀保护、GUI绕过均不在本次批准范围，作者已明确说明。作者工作树未修改，git status为空。
