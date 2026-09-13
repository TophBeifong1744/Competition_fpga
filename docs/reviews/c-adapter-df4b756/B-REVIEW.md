# B独立复核：C转接板首批四路实录与几何

2026-09-13。结论：**通过，仅接收hardware-audio/diagnostic材料**。没有采集核心或活动RTL变更，不批准正式M1、定位、波束、完整H3或整机。

## 身份与范围

- 仓库TophBeifong1744/Competition_fpga，分支codex/toph/c-adapter-first-20260913。
- 审核SHA：df4b756ba49a2d161c03869a0a4a28034dad15b0。
- 作者基线：99cf1dc2c1e7e2bd60ca843839d47906f9b84770。相对此基线仅新增task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/c-adapter-first-20260913下66文件。
- 独立工作树F:/NUEC/review-worktrees/c-adapter-df4b756固定该SHA，原始字节与Git对象逐项一致。
- 网络最初连接重置/超时；随后限定分支fetch成功，origin作者分支确为审核SHA。直接ls-remote曾超时，最终发布核对另记，不将失败记录写成成功。
- HANDOFF中的“未提交”属于编写时状态，以准确审核SHA为准。B记录放本目录，未加入或覆盖作者清单及冻结delivery。

## 实际命令与结果

Python为C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe（3.12.14），NumPy 2.3.5。先读HANDOFF.md、GEOMETRY.md、REPRODUCE.md，再核源码、记录和原始数据。以下在固定工作树仓库根执行，BATCH代表上述批次路径，PY代表该Python：

```text
PY -B BATCH/verify_delivery.py BATCH/delivery-01 --report F:/NUEC/review-evidence/c-adapter-df4b756/archive.json
PY -B task-packages/PKG-B-ALG/payload/model/python/h1_reader.py BATCH/delivery-01/c-adapter-quiet-20260913-01 BATCH/delivery-01/c-adapter-speech-20260913-01
PY -B -m unittest discover -s task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source -p test*.py -v
PY -B F:/NUEC/review-evidence/c-adapter-df4b756/independent_audit.py F:/NUEC/review-worktrees/c-adapter-df4b756
```

归档入口ARCHIVE_CHECK_PASS_NOT_ACCEPTANCE，H1入口PASS_FORMAT_ONLY；17/17导出器正负例通过。B独立脚本不调用作者解码器，直接解析BIN/CSV/WAV、计算FNV/RMS并核对Git及清单，结果PASS。脚本和原始回执存本目录。

## 数据与清单

66个Git新增文件全部等于审核对象；批次65项PACKAGE-SHA256加自身、delivery的40项SHA256加自身、received的14项SHA256加自身均检查精确文件集合和哈希。绑定的导出器、读取器及接口文档哈希通过。基线至审核SHA没有旧杜邦线记录或采集核心变更。

| 项目 | 安静 | 人声 |
| --- | --- | --- |
| 原始组数/字节 | 32000 / 1024000 | 32000 / 1024000 |
| 原始编号 | 17238..49237 | 16542..48541 |
| FNV1a32 | 890EA19D | 07739375 |
| 段内缺号、flags、reserved | 全0 | 全0 |

128包×8000字节、最终DMA 0x1002、源状态0x0A及串口校验由入口复查通过。独立BIN解析确认signed24/int32范围、编号连续、七列CSV每值一致；两段是独立Run，不拼共同时间轴。received与delivery的BIN/串口/WAV逐字节一致。8个WAV均为32000样本、单通道16bit、配置48000Hz，逐样本等于round(PCM24×12/256)，无新增剪切；该统一试听增益不作用于原始BIN/CSV。48000Hz和0.666667s为配置值/计算值，并非仪器实测。

## 原始幅度诊断

仅在B统计中去均值，未改变任何文件。mic0..3的安静RMS为7199.37、7394.96、7866.23、6874.53；人声为7952.59、8608.17、8098.36、7706.25，增幅10.46%、16.41%、2.95%、12.10%。原始均值及峰值见independent.json。

四通道非恒定且无完全相同通道对；零延迟相关系数安静约0.866～0.934，人声约0.633～0.923，均有较强共同成分。现有两段短录音不能将共同成分归因为声场、背景或电气耦合，也不能据小幅RMS变化判断故障或声学通过。没有独立声源参考、逐只激励或精确同步测量，不据通道相异宣布物理映射/精确同步已验证。

## 加载与几何

独立核对loading-record的8文件长度/SHA；XSA内bit和ps7_init.tcl与归档文件逐字节相等。ELF确含Sep 11 2026、18:23:59及four-channel-c-adapter-v1，与串口一致。launch保存resetSystem、PL配置、ps7_init/post_config、核0复位及ELF加载设置。磁盘配对、操作者声明、串口相容这三层证据均保留；没有JTAG全程日志或设备读回，不能证明设备加载身份已被密码学绑定。RX及end仅核对现有源码/记录，未新增构建或实板边界实验。

40mm边长来自操作者报告；共面正方形另有操作者声明。mic0原点、+X朝mic1、+Y朝mic3，四点模型[[0,0,0],[0.04,0,0],[0.04,0.04,0],[0,0.04,0]]及独立几何/config版本一致。四边相等本身不证明正方形；工具、误差、对角线和独立测量未知。

声源约10cm、−45°、近似同高以mic1为参考，不能替代mic0或阵列中心的精确真值。这是近距离输入，不直接用于远场角度验收；照片和操作者反馈不替代精密几何、电气或声学映射实验。

## Standards

无诊断归档接收阻断。只读入口、依赖哈希和冻结清单符合AGENTS及三人工作流。一个非阻断使用限制：prepare_delivery.py的输出保护只要求批次内不存在的新目录，未排除delivery-01/new-child；误用会污染冻结集合。因此本轮没有运行重导出，也不批准它作为通用冻结目录安全入口；以后如需重导出，应按REPRODUCE使用并列的新delivery-02。本次不修改作者方案后自审。

## Spec

无阻断或越界声明。几何、加载证据及诊断身份与用户范围一致；数值现象及所有未知项保留。

## 未执行与集成边界

未访问A的F盘原件、实际one或板卡，未运行prepare_delivery.py、新构建、Vivado、上板、设备读回、试听主观验收或定位算法。来源标签以操作者记录和归档支持，不把解析通过当物理来源证明。

原件留既有批次任务路径，不迁活动RTL。合入前main为8d348268dcd70bea963318cd852fbfb35abcd702；仅合入作者66文件和本B记录目录，其他成员工作不改。发布、回归和批次收尾在下节追加。

## 批次收尾：本地已完成，网络发布待完成

| 项目 | 实际状态 |
| --- | --- |
| 本地合入 | 2c76526a3fd631735f0d73120924055f4e69bb78；随后9609e792f7bdb4c4645f0cb52448e0e39d6602ed补交被通用日志规则忽略的6份B回执 |
| 合并后验证 | main工作树重新归档检查、H1两段读取、17项测试、66份Git/三层清单/独立数值检查全部通过，见main-*回执；原包字节未变 |
| 本地材料 | 补齐6份日志后，本批跟踪/暂存修改0、未跟踪0、忽略0；有用材料全部在批准包或本B目录正常跟踪，没有以改清单或忽略规则掩盖缺项 |
| 共享目录 | F:/NUEC/develop仍为feature/member-b-algorithm，HEAD57b86e0；其他任务52项已跟踪差异、146项未跟踪全部保留。本批路径状态/忽略0，未切换或重置该目录 |
| main对齐未完成 | 盘点时本地main9609e79、origin/main8d34826，领先/落后3/0（含作者提交和合入提交）；本次收尾文档还会增加本地提交。直接远端查询与push持续443连接超时/重置，不能声称origin/main是当前实时远端或本批已经发布 |
| 网络实际 | 初次fetch重置，第二次443超时，第三次HTTP/1.1限定fetch成功并核对作者origin为df4b756；之后多次ls-remote失败，直接push也连接失败。连接器只读备用查询返回404，未据此推断仓库不存在。系统DNS可解析，但连接未恢复；未改系统网络配置 |
| 证据位置 | 本目录保存脚本和实际日志；外部原始回执F:/NUEC/review-evidence/c-adapter-df4b756。完整无关文件名清单只在外部batch-full.json，SHA256 ecaa43bb69406c46e853c78437477099bb41982034fd1528ce77d87b38b74a37；本目录batch-summary.json给出计数 |
| 清理 | 暂无删除。审核工作树干净且无忽略项，可由df4b756恢复；因发布未完成暂保留。作者短期分支、A的F盘原件/实际one/pub和其他任务均未删除，不代签A设备同步 |
| 遗留与下一步 | 技术阻断0、本批未说明材料0；待完成1项发布收尾：网络恢复后由B非强制push main，核对直接远端与本地/跟踪一致，再按授权检查清理本次短期分支/干净副本。最终main号以成功发布后的回报为准 |

此记录截至本地收尾快照，明确不是“已发布并收尾完成”。后续若网络恢复，以后续实际发布回执补记，不将本次失败覆盖为成功。

## 发布恢复与最终收尾

用户通过GitHub Desktop推送后，B再次fetch成功，并直接ls-remote确认main为004dfb8ab251a5efdfa0b74dd292237f251ec41c；实际共享仓库的local main、origin/main同SHA，领先/落后0/0。此前网络失败保留为历史，本节更新最终状态：**已发布，B侧批次收尾完成**。

- 批准df4b756已是main祖先，原66文件与批准提交无差异。之前在合并位置完成的17项测试、H1读取、归档及独立逐值/清单验证仍适用；此次仅补文档，无新构建或上板。
- 本批修改/暂存/未跟踪/忽略的未处理有用材料0；main工作树干净。共享feature工作树仍有其他任务52项已跟踪差异和146项未跟踪，全部保留，本批路径差异及忽略0。
- 删除前确认F:/NUEC/review-worktrees/c-adapter-df4b756准确路径、无跟踪/未跟踪及全目录忽略文件；已用git worktree remove清理。可按准确df4b756重建，脚本中该路径为历史运行位置。
- 本次获授权短期分支codex/toph/c-adapter-first-20260913仍为df4b756，全部提交已入main、无独有提交，本次诊断交付已结束；已用指定SHA的lease条件删除远端分支，防止删除并发新增内容。B本地没有同名分支。需要恢复可由main历史中的df4b756创建引用。
- A的F盘原件、实际one、pub、其他任务及共享目录材料未删除；A侧同步未代签。实际main工作树是当前使用仓库，保留，不作为临时副本删除。
- 新盘点见published-summary.json；完整无关文件名仍只保留外部published-full.json，SHA256为4f7645a8a9e25a88f39d6251abb9939d23a0c2b01e729bd3bc355c3fb3590630。

本收尾记录补提交后再次核对直接远端、共享local main与origin/main，最终SHA在用户回报与外部final-alignment.json记录，避免为记录自身SHA循环提交。
