# FFT29 剩余136帧覆盖结果

2026-09-12；状态：作者实现及自检完成，待“拓芙工作执行”检查交付、发布新SHA，再由B独立复核。
本分支没有提交、推送或合入，不自行宣布独立验收通过。

## 结论

本轮新增136个归档case全部完成前向FFT29位精确对照，0个实虚整数码不一致，最大码差0。
与原限定批准的60帧按准确case ID合并后，196/196帧均有对应前向FFT证据，无重叠、无遗漏。
**这是历史60 + 本轮136的合并，不是本轮重新执行全部196。**

| 口径 | 原60帧（历史） | 本轮新增136帧 | 合并 |
| --- | ---: | ---: | ---: |
| 唯一归档前向FFT | 360 | 816 | 1176 |
| 唯一实虚整数码 | 737280 | 1671168 | 2408448 |
| 背压重复 | 1 | 1 | 2（跨两轮） |
| XSim变换总数（含重复） | 361 | 817 | 1178（跨两轮，不是本轮次数） |

本轮含重复共836608个复数点、1673216个实虚整数码，全部一致；
817个状态记录的overflow均为0，job/bin顺序、TLAST、未知值、状态数量及既定背压保持检查通过。
额外重复为case001/ch0，沿用原每31点插入2周期输入间隙、每7周期停收1周期的方式。
这是有限背压实例，不证明任意阻塞时长、强制overflow注入或恢复行为。

本轮只有用户执行的1次XSim；工程实现随后执行输入核对、比较和归档复查，
没有再次启动仿真。仿真结束于60182750 ns（60.182750 ms），不是实板耗时或整链吞吐测量。

## 来源与输入绑定

- 请求main基线：e670eef5de66e85981db8880bee6d41d9afb3a18。
- 实际工作HEAD：bb82de16a33751fb684243a19132dbb6b5736d91，为上述基线后代。
- B固定来源：bff45e7bbedab321fc4815e1432f1575c750edc4。
- 原A60帧及B回执：父包evidence/run01/check.json、
  PKG-B-ALG/tasks/phat-fixed-03/closeout-01/a29-review-01/README.md；
  对应限定批准A提交c0b5f8fb44643e81d8c4e6f0be457dddeae9758e。
- 从旧selection/check的case集合求差，新增136帧；逐个核对Git blob ID、B manifest SHA-256及frames中的NPZ哈希。
- 输入直接是归档windowed int64左移4位；检查实际XSim读入的inputs.mem等于该整数打包，
  虚部及padding为0。expected.npy逐项回查归档wide29_raw_fft，没有重新生成声源、PCM或窗。
- 原包155项文件、旧清单及历史证据字节不变。准备阶段清单也不重写，
  后续演进的README/准备入口/归档保留规则原字节由PREPARATION-HISTORY.json映射到只读snapshot。
- 为支持发布新SHA后的复现，只调整准备入口的基线判断：允许本extension的新提交，
  仍拒绝原FFT29目录其余已提交变化并验证旧155项哈希。该调整没有改动用户已执行的输入、TB或FFT配置。

## 实际配置与协议

实际为Vivado/XSim2025.2 SW6299465 / IP6300035，
xc7z020clg400-2、100MHz、xfft9.1 revision15、1024点、Radix-2 Burst、
S29输入/输出分量、24位旋转因子、convergent rounding、自然序、nonrealtime。
配置字0x0AAAAB、十级各右移1位不变。

本轮XCI的全部component_parameters和model_parameters与原配置完全一致。
编译文件列表、compile.log和TB源哈希互相对应。
新simulation-only VHDL wrapper省略了旧综合wrapper的X_CORE_INFO、
CHECK_LICENSE_TYPE、CORE_GENERATION_INFO三组声明/属性（共6条）；
除此之外的端口、generic及逻辑文本一致。没有借此忽略其他差异。

TB只有容量、作业数及超时上限适配；
check.py和collect_simulation.py只改变成功标记的361→817，原逐码比较/无损打包逻辑复用。
原9项比较器正负例加4项适配约束检查再次通过（13项），日志保留。

本轮没有新综合、布局布线、资源预算、bitstream或上板。
历史资源/时序仅引用父包evidence/run01/reports/，不重标为本轮结果。

## 证据入口

- [coverage.json](evidence/run01/coverage.json)：准确新增case列表与历史覆盖合并。
- [per-case-results.json](evidence/run01/per-case-results.json)：136个case逐项结果。
- [per-job-results.json](evidence/run01/per-job-results.json)：817个job/channel逐码统计。
- [check.json](evidence/run01/check.json)：复用比较器的原结果。
- [configuration-check.json](evidence/run01/configuration-check.json)：实际IP/编译源绑定。
- [input-index.json](evidence/run01/input-index.json)：NPZ的固定提交、blob与SHA-256。
- [simulation/](evidence/run01/simulation/)：原始CSV无损gzip、工具日志、实际编译/展开/启动命令。
- [vectors/](evidence/run01/vectors/)：实际输入、expected、job-count、selection，便于不依赖临时目录复查。
- [user-run-screenshot.png](evidence/run01/user-run-screenshot.png)：用户提供的完成截图。
- [artifact-sha256.json](evidence/run01/artifact-sha256.json)：本轮归档产物哈希。
- [REPRODUCE.md](REPRODUCE.md)：只读复查及从零重新仿真的命令。
- [SHA256SUMS.json](SHA256SUMS.json)：本extension最终文件清单，不覆盖旧清单。

完整原运行保留于E:/fft29-coverage-01，不覆盖、不删除。
归档未复制136个NPZ的第二套研究包：准确原件在仓库B归档与固定Git对象中，
临时运行目录保留其必要快照，输入索引逐个绑定；归档输出可独立从这些原件复查。

## 失败与限制

先前输入审计脚本把解压哈希误读为manifest字段，失败版本及输出在failed-input-audit-01；
改为按B packing读取后通过。独立Tcl解析器探针因Python运行时缺init.tcl未完成，
原输出保留；随后用户的真实Vivado/XSim运行通过，不把探针失败改写为成功。
本轮未发现FFT码不一致或仿真失败，未修改golden。

六麦仅为合成离线研究输入；不扩展真实四路采集，不修改one、CIC、H1、reference25、
PHAT、IFFT、跟踪器、默认算法或公共右移RTL，不恢复C004-R2或启动005。
全部逐码一致不代表定位精度、完整定点链、任意输入/溢出处理或H3通过，
也不新增9月16日阶段验收门槛。
