# B独立复核：中心参考目标输入

2026-09-15，结论：**通过，仅接收四路hardware-audio/diagnostic输入及附属说明**。

审核SHA为f9768b80e5718dcf29baf48015305780f4b9b8e8，远端分支codex/toph/center-target-20260915；发布基线09ecf267813e1ac289dae9358d9e097a87906c86。fetch和直接ls-remote确认分支准确SHA及main基线后，在F:/NUEC/review-worktrees/center-target-f9768b8固定detached工作树复核。

作者唯一批准路径为task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/center-target-20260914/。相对基线仅新增该目录76文件，工作树原始字节全部等于审核Git对象。README/HANDOFF的“未提交”属于编写时状态，不能替代准确发布SHA。B证据另放本目录，不覆盖作者清单或delivery。

## 实际执行

先读README、HANDOFF、INPUT-RECEIPT，再读REPRODUCE及源码/证据。使用Python 3.12.14、NumPy 2.3.5，PY为C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。仓库根执行，BATCH为上述批次路径：

```text
PY -B BATCH/finish_capture.py --verify BATCH/delivery-01
PY -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py BATCH/delivery-01/c-center-target-20260914-01
PY -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py OLD/c-adapter-quiet-20260913-01 OLD/c-adapter-speech-20260913-01 BATCH/delivery-01/c-center-target-20260914-01
PY -B F:/NUEC/review-evidence/center-target-f9768b8/independent_audit.py F:/NUEC/review-worktrees/center-target-f9768b8
```

OLD为同一four-channel-diagnostic-01任务的batches/c-adapter-first-20260913/delivery-01。四路任务source目录执行：

```text
PY -B -m unittest -v test_export test_c_capture_gate
```

结果：ARCHIVE_CHECK_PASS_NOT_B_ACCEPTANCE；单段及三段同会话均PASS_FORMAT_ONLY；17/17测试通过。独立脚本直接用NumPy解析BIN、重算FNV和CSV/WAV，不调用作者解码器，PASS。原始控制台回执及脚本见本目录。

## 文件、配对及数值

- 包清单75项加自身共76文件；delivery清单28项加自身；preflight-01/02各15项加自身，精确文件集合和全部SHA通过。
- 六项dependencies逐项与仓库文件核对通过。--verify本身未做此外部校验，因此B另行完成。六项不是全部传递依赖：导出器还读mapping JSON，最终adapter_interface由旧冻结metadata覆盖；未据此声称所有运行环境依赖完整封装。
- 两次预检各13份源码快照与各自report声明SHA一致；版本loading八项SHA一致，XSA内bit/init与归档对应文件逐字节匹配。ELF包含Sep 11 2026、18:23:59及four-channel-c-adapter-v1，与串口相容。没有读取A本机原路径。
- 本段32000组、1024000字节，编号17413..49412连续，独立FNV=F55CC8CE。128包均8000字节且DMA_SR=0x1002；源状态0x0A、同步/overflow、逐路统计由配对门/verify核对。flags/reserved全0，signed24符号扩展有效。
- 七列CSV每值等于BIN，原ID/PCM保留，无补样或拼接。4份WAV均32000样本、单声道PCM16、配置48kHz，逐样本为round(PCM24×12/256)，共同增益12，无逐路归一化或新增削顶。配置采样率/0.666667秒不是独立测频。
- 独立去均值RMS仅作为统计为14317.52、14139.55、13701.13、14127.21；未改原值。各路峰值及均值见independent-success.txt，不从幅度统计推断声学通过或SNR改善。

## 来源与验收边界

新段是操作者报告的现场人声；嘴部位于阵列中心+X、距中心1.5m、约同高，未独立精测。mic0仍为坐标原点，模型中心为(.02,.02,0)m，不能混同。测量方法、数值误差、内容/声级、发声起止和活动样本区间未知。9/15仅收到/处理日期，录制时刻为null。旧9/13手机歌曲及超重低音更正只在本批，旧原件未改；未借用旧试听反馈。

磁盘、launch设置、串口与数据配对支持记录一致性，不等于本次设备加载读回。未取得独立JTAG全过程、干净/噪声参考，不批准SNR收益、定位精度、远场、波束或整机。硬件前端已含CIC3/R64/乘32/饱和，不把主机未额外处理称为全链无DSP。

M1-NEXT仅交付连续采集提议，本提交未实施连续模式，未作为新增门槛。批准材料留原任务包，不迁活动RTL，不夹带Skill或其他任务。

## Standards

无阻断本批诊断归档接收的问题。--verify只读；作者新导出和check_package已有输出拒绝，失败保留。B未运行导出、inspect_current或已有输出的check_package。其A盘依赖检查不冒充本机重现。未批准这些脚本作为任意输入/嵌套输出的通用安全入口。

## Spec

无阻断。数据和同会话配置核对通过；声明正确分开中心参考、原点、报告精度、加载身份及未实施连续模式。下一排期说明不属于本次新增验收门槛。

## 空白提示与B检查失误

diff --check未通过：本机默认还将冻结CRLF回车标为空白；显式core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol后为102处，全部位于三套memory.map/ps7_init.tcl快照，退出码2。默认及显式输出另存；未改原件或把该项写成通过。

B补充脚本最初读取Git输出采用Windows默认GBK发生解码异常，随后原102计数断言受CRLF设置及三条组合类型提示漏计影响；改为显式UTF-8、明确CRLF配置及按诊断行计数后完整通过。失败输出independent.txt、independent-pass.txt、independent-final.txt保留，作者数据/清单完全未变。

## 未执行与集成

没有新构建、Vivado/板卡操作、A盘原件检查、加载读回、连续模式、主观试听、声学真值或增益验收。原17项为软件测试，不是RTL或实板测试。

合入前实际main工作树F:/NUEC/review-worktrees/member-b-to-a-pkg-b-alg干净，HEAD等于09ecf267基线。仅合入准确作者范围和本B记录；集成后相称复跑及发布收尾另记。A共享目录未提交工作不属于B代签范围。
