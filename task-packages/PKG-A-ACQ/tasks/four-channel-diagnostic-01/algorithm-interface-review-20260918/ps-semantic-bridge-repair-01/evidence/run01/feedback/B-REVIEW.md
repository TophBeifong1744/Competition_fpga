# B 独立复核：PS语义桥C候选

结论：**NEEDS_FIX**，不合入C候选。准确受审SHA fbbaa161098582ba1e5e112b86d39533769bb3e7；分支codex/toph/ps-semantic-bridge-20260921，父949d7a0ad040975290aa4c3b692e1e0188f6af63。实际日期2026-09-21，采用9/17增量复核规则。原C候选首次独立审，不把a7f70c5 Python返修批准继承给C。

## 版本、范围与完整性

首次网络fetch/ls-remote连接超时；重试fetch成功，直接远端候选精确匹配fbbaa16，main当时eb3a4482d9bdf9812b20e102fdb5af0d66069813。独立detached短路径F:/NUEC/r/psc；原件未修改。相对父1784新增：1481候选包文件+303发布材料；无旧文件修改。1479项闭集合清单及manifest摘要通过，全部新增Git字节一致，32历史绑定/8唯一Git来源匹配。

按PUBLICATION在该副本执行git restore --source=0abdc91c57787b7c868a797b88f35129de169faf --worktree -- task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923。该准确旧依赖仅用于归档保护检查，不暂存、不替换为a7。原f879/B/core/coord/main对象按run_host绑定使用。

## 实际执行

Python3.12.14/NumPy2.3.5，主机GCC8.1.0 x86_64-win32-sjlj，非作者GCC16.1。

1. 仓库根 `python -B <候选>/tools/seal.py --verify`：PACKAGE_VERIFY_PASS 1479，digest e774f248f3995839f952db5c9d18eafeb3b7ece02f3897102cead1a65ace75b2。
2. `python -B <候选>/tests/run_host.py --cc F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe --out F:/NUEC/r/psc-run01`：退出1。O0编译在旧MinGW printf I64/%zu兼容性处被-Werror拒绝，未计测试通过；原日志保留。
3. 同字节源码，包外gcc-ansi.cmd仅加-D__USE_MINGW_ANSI_STDIO=1，保持全部警告/断言：`python -B <候选>/tests/run_host.py --cc F:/NUEC/review-evidence/ps-bridge-fbbaa16/gcc-ansi.cmd --out F:/NUEC/r/psc-run02`。退出0，33/33对照通过；O0/O2各9组、27131断言通过，不重复累计。sizeof bridge=178856B、align8，只属本机布局。
4. B spec/probe.c直接和准确ps_bridge.c编译O0/O2执行，输出一致，确认下面PSB-B-01/02及六项控制路径。standards/generation_max.c编译执行确认PSB-B-03。脚本退出0表示成功记录缺陷，不是被测合同通过。源码、原stdout在报告同目录。
5. ASan+UBSan、UBSan构建均因本机缺运行库失败，NOT_RUN，不计通过。未运行ARM/BSP、真实并发、RTL/CDC、Vitis、实板、旧FFT/录音/耐久。

## Spec：两项阻断

### PSB-B-01 [P1] 同批冲突完成在提交后被跳过，排列改变可消费性

ps_bridge.c第二遍先要求owner==PENDING；首片段满足required_status后立即转COMMITTED，后续同token片段只返回REJECT，未再检查binding/payload，也未撤销结果。

同批 `status=3,payload=7` → `status=1,payload=99`，dispatch=REJECT但take=OK得到7；反序take拒绝。把后片段改为错误binding也同样顺序相关。违反CONTRACT中非零status片段payload必须一致和同批错误先于提交的声明。不能以返回REJECT就声称已保护消费；commit观察hook也已发生。

请在任何commit前完成整批同事务的身份、配置、状态及payload一致性检查/聚合，确保冲突任意排列都不提交；补同token部分/完整、跨事务、重复片段及错误status等相邻回归，不仅改负例退出码。

### PSB-B-02 [P1] 当前session的越界槽error被归作STALE

ps_bridge.c第一遍将session不匹配与slot>=PSB_RESULTS合并continue。输入当前session、slot=PSB_RESULTS、error=true后，failed=0 active=1、只有STALE审计，未触发合同要求的“未知当前事务错误保守fail-stop”。正常slot但未知generation则停机，分类不一致。

请先区分旧session和当前session；当前未知事务error无论槽范围均按合同停止，旧session回调仍隔离。回归slot=4/UINT32_MAX、未知generation、释放后回调及与合法完成同批的情况。

## Standards：一项边界阻断

### PSB-B-03 [P2] 合法最大generation帧无法acquire

token_new允许++generation得到UINT64_MAX；frame_acquire用oldest=UINT64_MAX和严格小于比较，不能选择该帧。正常4×250行enqueue/pump后，仅按合同允许的有限计数白盒方式设置generation=MAX-2，再正常24行enqueue/pump：READY帧generation=MAX，acquire=WAIT，active=1 failed=0。

应选择第一个合法READY候选后再比较，或一致地保留最大值并在生成前明确fault；不能既发布又永久WAIT。补MAX前后和两帧先后次序回归。此为模拟边界，不声称实板已运行到2^64次。

## 已确认通过与限制

33项原对照覆盖H1解码、错误行ID基准/连续错误、fatal、多原因、N1024/H512、8份准确B golden和23个A场景，原错误历史保留。独立检查commit→CLIP/STOP/RESET→晚错均fail-stop；旧session错误不误杀新session；结果释放后当前session错误fail-stop；外部config变化不改变init复制快照。这些通过不抵消三项缺陷。

新Python a7f70c5仅作为既有合同语义参照，未代替C包原0ab来源，也未计为本C测试。主机串行模型不能证明异步status、时钟hook真实性、硬件背压或WCET；REALTIME_BLOCKED。只读hooks和内部字段不允许任意外部修改的前提保留。

规范轴发现1项边界缺陷；需求轴发现2项合同缺陷。集中反馈后保留完整证据，作者修复再增量复核；不边改C实现边批准，不把现有33/33或作者自检当准入。
