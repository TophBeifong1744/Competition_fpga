# B 回执：杜邦线四路真实输入诊断

2026-09-11。**结论：可接收（通过四路 diagnostic 数据交接与本轮离线诊断复核）**。未发现阻断本次用途的内容问题；以下通道与低频观察需保留，不能扩大为声学或整机验收。

## 1. 审核输入与获取方式

- 仓库：TophBeifong1744/Competition_fpga。
- 分支：`codex/toph/four-channel-dupont-diagnostic-01`。
- 固定审核 SHA：`d088e2c7deda9c505c094fd48d6f90bcd7f52807`；父提交 `e811c399adaa083d520bfda998f15fe86b445b9a`。
- 远端 API 分支头等于该 SHA；树为 `3b4dbfd4a464c986b2e8e5e9a7dbe598bec0a2be`。原始响应见 `F:/NUEC/review-evidence/a-dupont-d088e2c/remote-branch.json` 与 `remote-tree.json`。
- 直接 Git fetch 遭连接重置，未成功。本次使用固定提交的 Git blob 下载完整交付 ZIP，独立解压；此目录不是 detached Git worktree，不声称成功 fetch 或 checkout。未覆盖 develop 或以前的审核工作区。
- ZIP：`verified-delivery.zip`，3,797,025 字节；SHA-256 `a5d9bb8388d0921c53d254340030ae0b584111d7381b8a2d88a5c49079324721`，与发布说明一致。
- ZIP 内 72 文件：71 项负载和 MANIFEST.sha256.json。清单不认证自己或新增 B 输出；外层 README、B-START、.gitattributes、ZIP 也不在负载清单中。B 另按远端 Git 树验证全部 76 个发布文件的大小与 blob 身份，包含上述外层文件、72 个 payload 文件与 ZIP；全通过。
- 阅读顺序 B-START → 外层 README → payload/REVIEW → B-HANDOFF。原报告“未推送”和9878cca基线为历史状态，不改原件，以本发布 SHA 为本次数据身份。

获取失败记录：整仓 tarball 下载因仓库历史材料较大而中止；contents raw ZIP 请求返回 `transform: short source buffer`，保留的19字节文件不是有效 ZIP。这两份失败/不完整下载不用于任何结论。有效输入仅上述校验通过的 Git blob ZIP及固定树；完整原始 BIN、串口日志、metadata、CSV、WAV和构建快照均已取得。

## 2. 独立执行命令

工作目录：本 B-REVIEW.md 所在的独立解压包根目录。环境 Windows PowerShell；Python 3.12.14，NumPy 2.3.5；Python 可执行文件为 `C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`，运行时放在 PATH 首位。

确认 b-recheck-01 不存在后执行：

```text
python -B verify_manifest.py .
python -B b-reader/payload/model/python/h1_reader.py captures/dupont-quiet-01 captures/dupont-speech-01
python -B audit_capture.py --captures captures --reader b-reader/payload/model/python/h1_reader.py --output b-recheck-01
python -B audit_listening.py --captures captures --output b-recheck-01/listening.json
python -B b-reader/payload/tb/python/test_h1_reader.py
python -B source/test_export.py
python -B source/test_c_capture_gate.py
python -B F:/NUEC/review-evidence/a-dupont-d088e2c/independent_review.py
```

全部退出码0。前7条原始输出保存到 `F:/NUEC/review-evidence/a-dupont-d088e2c/01-manifest.txt` 至 `07-gate-tests.txt`；独立脚本与结果 `08-independent.json` 同目录。复现输出 b-recheck-01 完整留存。未重跑原导出器重新标记物理来源。

71项清单通过；读取器返回 PASS_FORMAT_ONLY；原始/串口/CSV复核通过；8份WAV转换通过；47项读取器、8项导出、9项配对门禁测试，共64项全部通过。测试夹具为合成软件回归，不计入真实录音证据。A脚本保留历史返回标签 PASS_DIAGNOSTIC_INTEGRITY_NOT_B_REVIEW；B是否接收由本报告明确裁定。

读取器 SHA-256：`104d15e41cc186b8622df8b0ce52b0aae9b06085eab5e0b982a4b0053c9b2fa9`。输入清单SHA及逐文件SHA在08-independent.json。提交的读取器日志为UTF-16，新结果为UTF-8，解析JSON相同；未以编码差异误判录音失败。

## 3. 格式、编号与原值

| 输入 | 组数／字节 | 原始 ID 区间 | FNV-1a32 |
|---|---|---|---|
| dupont-quiet-01 | 32000／1024000 | 17544..49543 | A34F540B |
| dupont-speech-01 | 32000／1024000 | 15798..47797 | 7B1E2B16 |

每段128包×8000字节，DMA_SR=0x1002，最终SOURCE_STATUS=0x0A；串口的包号、长度、样本量、端点、FNV及逐通道极值/零值/削顶计数与BIN一致。CSV所有原ID、四路码值、错误列与BIN逐值相同。每段内部编号连续，缺号/重复/倒退、错误行、同步错误、溢出和饱和flags均为0，保留字为0。没有段内重启迹象；不能由此证明停止/重启专项或全部物理错误均不存在。

两段是独立 acquisition，第二段起始ID较小不是段内倒退，不拼接共同时间轴。配置48kHz下每段约0.666667秒，实测采样率未知。

H1为ss-data-draft-0.3，四列mic0..3，原ID uint64；signed24、右对齐符号扩展int32、F=0。独立 `<QiiiiII` 解码也通过；所有PCM为32的整数倍，与CIC3/R64输出乘32相符。没有补样、重编号、增益、去偏置或滤波改写。

## 4. 各通道幅值及偏置

以下均为原始PCM码值，RMS原值含DC，AC RMS是去均值后的标准差；只在统计副本计算。

| 段 | 路 | 最小值 | 最大值 | 均值 | RMS原值 | AC RMS |
|---|---|---:|---:|---:|---:|---:|
| 安静 | mic0 | -19968 | 23424 | 771.69 | 6887.39 | 6844.03 |
| 安静 | mic1 | -24384 | 25216 | -477.43 | 7413.44 | 7398.05 |
| 安静 | mic2 | -24512 | 23616 | -97.28 | 7275.75 | 7275.09 |
| 安静 | mic3 | -20864 | 21952 | 842.62 | 6650.29 | 6596.69 |
| 人声 | mic0 | -456576 | 382848 | 1005.84 | 145623.84 | 145620.36 |
| 人声 | mic1 | -411392 | 327488 | 1557.24 | 138731.94 | 138723.20 |
| 人声 | mic2 | -448192 | 337536 | 910.60 | 147405.18 | 147402.37 |
| 人声 | mic3 | -502400 | 430656 | -289.50 | 162701.05 | 162700.80 |

所有通道饱和计数0、非常量，无完全重复通道对；人声最大绝对峰值仅约满量程5.99%。人声段AC RMS较安静段更高，但两段内容不同，不能称SNR改善、声压或增益标定。静态均值非零不单独证明硬件故障。

## 5. 相关性、频谱观察与下一处排查

对原始全段去均值计算零延迟Pearson相关；频谱采用4096点Hann窗、2048步长、每窗去均值、单边功率平均，频率按配置48kHz，分辨率11.71875Hz。不是校准PSD或长稳测量，详细矩阵和比例保留在08-independent.json。

- 安静段6对相关系数约0.8901–0.9675；四路最大非DC谱箱均46.875Hz，100Hz以下功率占比依次91.04%、91.00%、83.26%、91.53%。该谱箱接近50Hz，但短片段、窗泄漏及未测时钟限制下不能断言市电或供电是来源。
- 安静段mic2的4kHz以上占比约9.47%，其余mic0/1/3约1.55%、1.41%、0.56%。这是需跟踪的通道差异，不足以裁定坏麦、数据线故障或噪声来源。
- 人声段300–4000Hz功率约94.50%–95.64%；最大谱箱均796.875Hz。mic0/mic3相关约0.9909、mic1/mic2约0.9961，其余约0.8523–0.8845。数据不逐样本相同，但存在高度相似配对。共同声源和近距离布置可以造成高相关；相关性本身不能证明复制通道、物理接线映射或同步标定。

**建议下一处排查**：先记录实际四只麦到mic0..3及几何顶点的对应关系，在既有硬件安全操作安排内采用逐麦局部声学激励，观察各列相对响应，确认高相关配对仍是独立物理输入；再针对安静段低频共同成分及mic2高频差异做可控条件对照，保持供电/线缆/位置条件记录和原幅度数据。相关性不能代替映射记录。此为后续建议，本轮没有改变硬件、安排上板或修改滤波/阈值来掩盖现象。

## 6. WAV、来源与工程身份

8份WAV均单通道PCM16、48kHz、32000帧，按 `rint(PCM24*12/256)` 逐点相等，共同增益12，无新增饱和。仅为试听副本，不是原幅度H1或降噪收益。操作者反馈“人声清晰”作为主观反馈保留；B本次没有声称独立听过。

metadata的hardware-audio与Dupont来源说明属于操作者声明，有匹配串口/BIN及试听反馈支持；解析器不能独立认证物理来源。实际记录为杜邦线四麦，不是C转接板；配置名c-adapter不能替代实物证据。约40mm共面正方形为操作者描述，coordinates_m仍null，物理顶点映射、声源方向/距离及声学标定未知。未计算DOA，未扩六路。

build-snapshot原清单21项大小和SHA全通过；one bit、应用加载路径bit与XSA内部bit字节一致，one/platform XSA一致，XSA PS初始化与应用脚本一致；ELF含Sep 11 2026 18:23:59并匹配串口。

- bit：`37f6d55fbd1ce314245d189fbe2fa984477c6b61d26a2a23736b71305654605b`
- XSA：`71e7bf6d4fcb769582e5485660515b8f615b2027aa2ff18c1f8d3f67f9457baa`
- ELF：`c0b430e77d4d0d53d4ca0b4399fe69e0cd7865e5815ac3549b5d209d39e7192a`

这是快照关联与配置支持，不是事后实际FPGA加载状态的密码学证明；不套用build06旧哈希或把ELF时间说成bit构建时间。已有路由报告不等于本次重跑实现；四路输入/四路输出外部延迟仍未完整约束，声学同步、实测时钟、长期稳定及相关电气验收保持未通过/未知。

## Standards

阻断性标准违规0。配置、已有工具报告、本轮文件复算及操作者实录声明分开；历史原件、失败日志及合成回归夹具按用途保留。未发现需要修改交付代码的维护阻断问题。

## Spec

阻断性需求问题0。完成本轮要求的清单/可解析性、编号错误、逐路幅值/偏置/RMS/饱和、重复及异常相似检查和必要频谱诊断。低频、mic2高频及高相关配对为已记录的非阻断观察，无坐标条件下不推导角度。

## 最终范围与阶段状态

**可接收**这两段四路真实输入声明、原始数据、日志和试听副本，用于四麦diagnostic读取、数值和初步通道诊断。现在可以记录“已有四路杜邦线实录且B完成本轮诊断回执”，不再沿用“尚无四路录音”。

本回执不批准正式M1、完整H2验收、六麦FPGA接入、DOA精度、波束/增强收益、H3、C转接板实物或完整板级验收。主流程可据此处理本次H2四路诊断材料交接关闭，完整阶段验收仍按其范围单独裁定；定点/H3工作不因此停工。

原始输入和原清单未修改；仅新增B复现产物和本报告。未提交、推送或合入main，未修改默认算法/阈值或其他任务。未发现需先反馈A的阻断内容问题；本报告即供回传的B回执，未另向远端发布消息。
