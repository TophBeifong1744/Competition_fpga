# PWM 独立复核回执

2026-10-10。只读非作者复核人：`/root/pwm_evidence_review`（fpga_reviewer）。本页由协调者记录其返回结论，未改动产品或测试证据。

**PASS，范围仅为 PWM FUNCTIONAL_SIM。** 未发现新增 BLOCKER/HIGH 或需修复项。

| 冻结文件 | SHA-256 |
|---|---|
| board-prep/rtl/motor_drive.v | 5c1a62f19ed0f25c06f22e521df90161dcbe2f835e2bc2dfaaf1b37ff7b41aa9 |
| board-prep/rtl/four_mic_live_loop.sv | 21d4decb91e0850d2e7634f4dd1dcd212552e500151b1ec79d564d1bd9f101e4 |
| board-prep/verification/EVIDENCE-INDEX.json | 09a4d2fb9b318eebf926b56cb1c74635b4f39c4904e6bd6defdf7aa97a3a60e8 |

复核核对了索引散列、正常运行三阶段原生日志、独立数学检查器、整数原版逐拍比较、复位和命令边界、3 个检查器负例及 5 个非法参数用例。正常原始运行位于 `../board-prep/verification/runs/nominal-attempt5/`。

61.44 MHz 参数下，20 ms 周期为 1,228,800 拍；500/1500/2500/506 μs 脉宽为 30,720/92,160/153,600/31,089 拍。参考模型基于输入命令历史和时钟边沿，不读取 DUT 内部分频器。1/50/100 MHz 与冻结原模块逐拍一致。

XSim 对 Fatal 仍可能返回 0，负例判断核对的是指定 Fatal 内容；正常用例要求完整检查器结束且无 Fatal。早期工具环境失败被保留，不算 RTL 故障。

全部实例使用 10 ns 测试时钟：本证据证明所配置的边沿计数，不证明板上物理频率。完整 top/IP、板级展开、综合实现、STA/CDC、BAT 入口及真实运动未由本次测试验证。可以继续板级集成；不得据此标记整机或上板通过。冻结 PWM 未变无需重复此组测试，新控制和物理输出门控另按影响验证。
