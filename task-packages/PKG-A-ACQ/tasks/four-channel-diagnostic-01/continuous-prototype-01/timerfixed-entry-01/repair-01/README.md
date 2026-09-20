# TF-B-01～03 修复候选

2026-09-16。原审核 bbe39c38dc36ccb4c0492f492b86f6c46d885fbe；B反馈准确提交 53018f9256cd209136183679d28b8949b04536f2。已直接查询远端，按序读取PUBLICATION、A-FEEDBACK、B-REVIEW及实际反例。未自行合入main，仍须B独立复核。

## 逐项修复

| 问题 | 实现 | 验证 |
| --- | --- | --- |
| TF-B-01 / P1 | 原链接脚本ENTRY(_vector_table)与ELF启动地址、ARM对齐、_vector_table/_boot、可执行且文件支持的PT_LOAD、启动节/段映射及原启动字节绑定；实际Ninja展开链接命令与归档约定比较 | 原归档ELF通过；7种错误入口、非执行段、缺文件数据/仅4字节加载、向量符号偏移拒绝；额外-e/--entry等3种参数变异拒绝 |
| TF-B-02 / P2 | Windows参数解析后，只规范化编译器及已识别路径参数；保留选项、宏名/值和字符串大小写及分词语义 | B两组反例不再判等；补充宏值、带空格/字面引号、宏内路径字符串、路径大小写测试 |
| TF-B-03 / P1 | Tcl启动Python长驻keeper；锁住活动三产物/对象/源与配置证明，执行完整load检查后复制三产物；取得封存文件锁并在锁内复核哈希，才回传快照路径。活动文件可随后重新构建，封存句柄保留到fpga/source/dow/con返回 | 真实NTFS写入、替换、删除、目录改名拒绝；已有writer拒绝。原生Tcl+真实keeper/ELF、其余gate前提及硬件mock：两种活动ELF替换均未改变mock dow读取字节，bit/init同时替换也不影响；三种封存文件写入均被拒绝；默认dry及9个步骤故障停止/释放通过 |

只支持当前固定布局与工具命令，未知布局拒绝，不是通用ELF加载器。链接查询使用ninja -t commands，仅枚举命令、不构建。计时、分包、DDR及两槽合同不变；无本轮真实错误参数重新链接。

## 加载保护与限制

调用仍为 c1_timerfixed_load python app platform tools_bin record_root ?dry_run?，五个路径必须为绝对路径，默认dry_run=1。source仅定义过程；未取得受保护收据时不执行硬件动作。Tcl使用本次管道会话回传的封存路径，不重新推导活动文件名。快照保留，不自动覆盖或删除。

CreateFileW读取句柄不共享写入/删除；祖先目录句柄阻止路径被重命名。持续打开的句柄保护下载端再次打开期间的文件，不是普通锁标志文件或最后一次hash。既有writer、共享冲突、非NTFS、远程盘、reparse point或缺权限均失败关闭，不退回无锁加载；普通用户权限即可。

UTF-8/base64传递路径；管道读支持CRLF、写使用LF。PING只检查keeper存活，字节保护来自OS句柄。不防恶意管理员、杀死保护进程或篡改运行器；GUI直接Run仍可绕过。真实XSDB读取共享模式及下载尚未测试，不兼容时应拒绝，不能关闭保护。

参考：[Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)、[CommandLineToArgvW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw)。

## 证据与覆盖

- evidence/old-negative-run01：原B脚本在旧真实ELF上复现两种无效入口接受、两种不同参数判等。
- evidence/old-race-run01：B竞态脚本仅调整PACKAGE/TCL本机路径，原生Tcl、真实ELF、部分gate及硬件mock，两种错误下载均复现。B原脚本在review-inputs，原B反馈未修改。
- evidence/fixed-b-negatives01：reproduce_b_negatives.py只调整B脚本末尾旧缺陷断言，新结果为两种拒绝、两种DIFFERENT。无效ELF仅供解析器负例，禁止下载。
- evidence/run05：原18项Python、新14项修复Python、新6项加载Python（含14次Tcl场景）、父包10项及安全34项全部通过，共82项Python测试，不是82次构建或板测。Tcl输入/输出与参数、退出码另存loader-cases。
- 新加载回归中keeper、NTFS锁、Tcl及归档ELF真实运行；其他完整Vitis gate前提模拟满足，硬件全部mock。keeper_fixture.py是TEST ONLY，不是生产入口。
- 旧87项清单不变；修改的三个根文件原字节保存在originals，其余旧文件原地不变。新REPAIR-SHA256覆盖当前文件。根test_load.tcl属于旧exec协议，不能当新pipe协议覆盖；新版运行test_loader.py。
- B的spec/reproduce.py未运行、不计证据；没有新Vitis编译、完整现场gate、真实下载/采录、RTL仿真或综合实现。未增加M1/H3/长稳/阶段门。

## 失败与修正历史

1. 最初sandbox下祖先目录句柄被拒绝。未降低锁强度，普通用户权限复跑通过。sandbox工具输出未完整存盘，不称其完整日志已归档。
2. run01两个测试误改首个非PT_LOAD程序头。失败测试源已保存，改为按类型选择真实PT_LOAD后通过；不是放宽产品检查。
3. run02 Tcl夹具遗漏空base64参数。保留夹具原件后修正，并要求故障测试确实到达指定故障点，避免无关失败产生假通过。
4. run03暴露生产管道CRLF处理错误；改为读auto、写lf。run04通过，run05增加绝对路径限制和省略dry参数测试后再次通过。各轮完整输出保留。
5. 一次apply_patch同补丁删除/添加同路径被工具拒绝，未落盘；改为普通更新后成功。另一次文档补丁JS字符串解析失败亦未落盘。未删除旧入口。

## B复跑

在timerfixed-entry-01目录，Windows Python 3.11+，输出必须是包外不存在的新目录：

~~~text
python -B repair-01/verify_repair.py
python -B repair-01/reproduce_b_negatives.py <包外新目录>
python -B repair-01/run_checks.py <另一个包外新目录>
~~~

用TF_TCL环境变量指定本机原生tclsh；默认A既有AMD Git Tcl。无需编译或连接板卡。run_checks分进程执行并保存每组返回码；fixture只是已归档文件的临时测试输入，不创建Vivado/Vitis工程。临时fixture测试后回收，命令及输出保存。

B原竞态脚本期待旧exec协议及错误下载，不能以其在新协议下失败判断修复成功。新版回归实际读取mock fpga/source/dow文件字节并尝试写封存文件；B可在包外适配同等反例，不覆盖证据或旧清单。

## 部署与交回

修复仅在独立待审工作树，共享目录和F盘原平台/应用未覆盖。F盘CMake目前引用的仍是共享旧入口，不能宣称修复已经现场部署。通过后由工作执行先安全同步批准源码，再由拓芙选择原应用/副本及接入，重新生成受检记录，不沿用旧dry结论。

申请仅为三项入口修复及离线/归档/模拟证据；B有阻断先反馈，通过后按准确范围合入、回归、发布及批次收尾，不代签A共享main同步。不自行合入，不删除实际工程仍引用的入口。
