# a-input-boundary-0.1 证据与增量清单

2026-09-09；状态：A 整理、自检，待 B 技术复核及正式合入。没有修改或重新生成外部 Vivado 工程、RTL、IP、比特流、H1合同及 B 算法源码，不包含新的板测结论。

## 交付

- `../../payload/docs/input-scale-and-pl-ps-boundary.md`：确认表，未来目标 `docs/input-scale-and-pl-ps-boundary.md`；SHA-256 `3767353b34dd97e494b9ec1b80de288e8b83c989c12fbcdc0b5eb0e0eac49959`。
- `source-snapshot/`：外部工程关键源文件的原字节只读快照，不是新的活动 RTL 或可独立重建的完整工程。
- `check_input_boundary.py`：只读核对固定来源哈希，并调用 B 原有适配器验证标度关系。
- 本包 `HANDOFF-TO-B.md` 和活动 `docs/work-packages.md` 仅新增交接入口，不代表方案已审批。已有未提交接线候选及 README/REVIEW/manifest 修改保持不动，没有夹带纳入本清单。

## 外部源快照来源

工程根：`F:/College/verilog_digital_system/AMD/Competiton/one`。

| 快照 | 工程内原始相对路径 | SHA-256 |
|---|---|---|
| system.bd | one.srcs/sources_1/bd/system/system.bd | `0a46738f4e400b23a0a0eb944d568e7212e17e5c9c669e99974b441068eb9c64` |
| test_source.sv | one.srcs/sources_1/imports/rtl/test_source.sv | `9dcfed15189390a93e8ca0805aa31608c3dfabd384d1a620a213cfbcd207a677` |
| test_source_bd.v | one.srcs/sources_1/new/test_source_bd.v | `302cbd21dc8d23024c40c94d81bbbabf726965858a32c5ddffb10e1da5138392` |

system.bd 中 FCLK0 配置100 MHz，DMA stream32/memory64/SG关闭；包装层与 test_source 的 signed16 三拍码型结构相互一致。只作源配置核对，不将其视为当前下载 bitstream 身份、时序或真实录音的证明。

## 仓库公共依据

核对时 SHA-256：

- `docs/minimal-data-interface.md`：`5489c6945230d338e3836c8a5d3007ddaf2257190b4cad016615569ae2d0ca00`。
- `docs/architecture.md`：`04dc37bb61f3eb1e9da15c221ec8c81ce304b4f11563027635aaa6956254eac1`。
- `task-packages/PKG-B-ALG/payload/model/python/audio_frames.py`：`0ed77ea8db8834576c21206358a8d945b612a176cad742bb266d077ee2a79408`。

来源变化时，自检故意失败，须复核更新而不是忽略哈希。接线候选仍在独立待审增量中，本表没有以它证明电气或抽取参数已冻结。

## 复核命令

仓库根目录，使用带 NumPy 的 Python：

```text
python -B task-packages/PKG-A-ACQ/evidence/input-boundary-v0.1/check_input_boundary.py
python -B task-packages/PKG-A-ACQ/payload/scripts/check_h1_fixtures.py
git diff --check
```

第一条核对7个来源/交付文件哈希、BD模块身份，调用现有 adapt_h1 核对8个边界/标度码值及编号与输入不变。第二条仅重跑 A 的 H1 样例检查，不冒称 B 读取器整套测试。均不代表 PDM 增益、有效位数、采样时序、DMA板测或 H2/H3 通过。

本轮实际结果：上述三条均通过。首次自检发现本清单包装层 SHA 文本多写一个字符，按原文件实际 SHA 修正后复跑通过；没有改动源快照来匹配清单。H1 样例为 code-pattern 6行、restart 2行，15项是读取器测试计划而非本次执行了15项B测试。Git只提示现有LF/CRLF转换规则，不是检查失败。当前未提交/推送；由 B 复核准确交付后决定正式合入。
