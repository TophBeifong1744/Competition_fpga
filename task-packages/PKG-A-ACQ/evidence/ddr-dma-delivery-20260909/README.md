# DDR / DMA 任务二、三交付：待 B 复核

本批由 A 整理供 B 复核，不自行合入 main，不替代原 DDR 五模式测试记录。基线 main 为 e3f49050cb695beaa8e2ea869ae365a8135a6750；分支 codex/toph/ddr-dma-delivery。

## 范围与状态

- first_batch_20260909：任务二首批两包实板记录，每包 24 字节，总 48 字节、4 组。用户提供串口文本，程序报告数据匹配/错误为零。
- multibatch_20260909_partial：程序报告 1000 批、2000 包、48000 字节、4000 组、errors=0；实际日志仅 batch746..999（254 批/508 包），缺失部分不补造。用户已接受尾段证据，不再要求重跑。
- capture_20260909_01：任务三从用户提供的 DDR 实收输出提取 samples.csv，附 ss-data-draft-0.3 metadata。4 组编号 0..3；数据不是由 golden 生成。软件/硬件快照不能证明板上实际加载身份；用户粘贴日志不是串口原始字节。

每批 README 与 manifest 保留原件。原目录位于 C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06ff9-0287-7e00-b73d-abf12e6b3035/ 下 one_task2/evidence/ 与 one_task3/；此次只归档副本，不修改正在使用的 Vivado/Vitis 工程。

## 本次整理验证

三份清单共 64 个文件条目 SHA-256 核查通过。任务三 validate_capture.py 在交付副本重跑 PASS_FORMAT_AND_PATTERN：CSV 与粘贴日志一致、12 个实收字解析与 CSV 一致、独立预期码型一致、4 组、零错误行、无缺号。复跑只写 validation.json，不改变 CSV/metadata；原始副本位于上述来源目录。

## B 复核入口

用具备 NumPy 的 Python，在本目录执行：

```powershell
python -B capture_20260909_01/validate_capture.py
python -B capture_20260909_01/reader/h1_reader.py capture_20260909_01
```

建议在副本执行第一条，保留交付中的 validation.json。不要运行 archive_current.ps1 重新采集本机文件覆盖冻结快照；该脚本仅保留来源记录。硬件/软件目录内的本机路径不保证移机可直接重建，重建需匹配 Vivado/Vitis 2025.2、XSA 和 BSP。

请 B 核对数据来源、编号/符号扩展、保护区/缓存与 DMA 状态、包长、日志缺口和文件身份，再填写审核提交 SHA、复核结果、允许合入范围及限制。时序/Hold/DRC 和完整工程验收不因当前数据通过自动完成。

所有数据均为 hardware-test-pattern / diagnostic；48 kHz 是名义接口占位而非实测采样周期，坐标 null，禁止声学推断。不代表麦克风录音、H2/H3、连续实时采样或正式采集验收通过。未包含 H2 准备计划或麦克风接线任务改动。
