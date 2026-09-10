# C-RTL-003 独立功能验收

日期：2026-09-10。对象：d41ee30f28d81fa2e48164782843b5bf10657148，C 分支的 v1.0 交付。

**结论：规格与功能验收 PASS，无需功能返工；待 B 正式复核。** 不代表总工程接入、综合或时序通过。

## 证据

- 作者清单18个文件的SHA-256和字节数全部匹配，测试前后保持一致。RTL SHA-256：3dd6504e455b31322b20732e3114879df772a90233618bb744498b701dae47b3。
- 原五位宽测试使用Vivado/XSim 2025.2、SW Build 6299465重跑，1887次128位比较全部通过，561 ns结束。[日志](logs/author/simulation.log)。
- 验收方另写[测试平台](tb_review.sv)，覆盖全部2～32位参数、逐位/符号组合、每位宽512组固定种子随机输入；2位四路256组合、3位四路4096组合穷举。24967次128位比较通过，4649 ns结束。[日志](logs/independent/simulation.log)。
- RTL为纯Verilog连续连接，四个槽位及各路符号位正确；32位参数的零长度扩展可编译。无状态、缩放、饱和、截断或附加握手。
- 全位宽和小位宽穷举不等于32位全输入空间的形式证明。以上为数字码型验证，不证明采集同步、物理接线或声学效果。

## 复现与原件保护

运行 [run_review.ps1](run_review.ps1)，传入工具bin路径和一个尚不存在的包外OutputDirectory。脚本先将作者RTL/TB按Verilog编译并复跑，再以SystemVerilog编译独立TB；逐步检查退出码、最终PASS和失败标志。各运行目录保存xvlog.log、xelab.log、simulation.log，不提交缓存。

```powershell
./run_review.ps1 -VivadoBin '<Vivado2025.2>/bin' -OutputDirectory '<new-output-directory>'
```

作者run_xsim.ps1会归档并回写submission/logs，本次没有直接执行它，而是在包外执行相同工具步骤。原README中“不推送远端”是作者当时操作说明；本次实际已核实远端head为上述提交，不改写作者历史文本。

## 语言与接入状态

遵循项目docs/rtl-language-and-bd-integration.md（rtl-bd-policy-1.0）：核心为pcm4_signext_pack.v，端口普通packed向量，无额外依赖，模块接口对应C-RTL-003操作单v1.0；SAMPLE_WIDTH默认24，合法2～32，四路signed输入/四个32位槽，右对齐不缩放，无时钟复位。

该.v核心是未来Module Reference的候选入口，不需要为了后缀额外包装。**实际BD添加、参数/端口识别、Validate Design均NOT_RUN**，留给后续受控集成；不追溯增加003原任务未要求的否决项。综合、布局布线、时序、板测、DMA接入也均NOT_RUN。

本次只新增验收材料及下一项操作单，不改001/002/003原件，不更改正式分工，不操作共享one/BD/PS工程，不合并main。工具原始日志保留行尾空格和原始字节；文档及测试源单独做空白检查。
