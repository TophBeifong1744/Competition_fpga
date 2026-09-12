# B Spec 轴独立复核

审核 SHA：d0ce1c28aac3e101a262036b2321f4170d34f45c。基线：050d06f5dc6fed4fa476e72fa416e9736bc7fef3。
结论：在声明的已知采集正文、固定七项合同、可信 GCC/BSP/链接输入范围内，源码审查未发现本轮阻断；原 BASE 改动仍获假 PASS 的机制已关闭。

## 实际执行

读取 AGENTS.md、repair_ps_contract/README.md、commands.json、build_current.py、ps_contract.py、test_ps_contract.py 和原 B ddr_counterexample.py；查看两版本源码 diff。运行 `python -B inspect_linked_ranges.py`，仅解码归档真实 ELF，结果保留于 linked-ranges-result.json。本轴未执行 AMD、真实重新编译、完整 build 或板级验证。原反例及 21 项回归由主复核轴运行，不在此冒领测试结果。

## 关键证据

- ps_contract.py:39–62 将七个限定宏行之外的正文绑定固定 SHA，未知正文、重复/条件定义、旁置代码改变均不能作为已知采集源放行。
- ps_contract.py:209–248 先包含实际 staged main_four_capture.c，附加只读合同常量；一次真实预处理生成 .i，明确以 cpp-output 编译该 .i，链接同一个 .o，再直接从 ARM ELF32 符号数据读取合同并比较。未将版本字符串、日志、旁置 JSON 当最终合同。
- build_current.py:355 在 ps-only 分支和 Vivado 调用之前强制调用 compile_bound_ps；失败进入 BUILD_FAILED，不存在完整 build 的跳过参数。发布 ELF 来自已检查的 ps_check 输出。
- ps_contract.py:170–202 校验实际 ABI、DDR/XSA/HP0 可达范围、组数/分包/保护区和固定合同；全部非空 SHF_ALLOC 与 PT_LOAD 内存区间必须位于 BASE 前，end 必须覆盖最大分配末端。end=BASE 用 <= 合法，越界及伪低 end 拒绝。
- 独立解码归档 ELF：BASE=0x01000000，end=0x00112630，__stack=0x00110e30，__undef_stack=end；实际 .heap/.stack 和各堆栈边界符号均在 RX 前。本次归档合法布局满足检查。

## 范围边界

当前检查不构成任意链接脚本认证：检查 .heap/.stack 分配和 end，不独立绑定所有 startup 堆栈符号到这些分配。源码明确采用可信链接输入、已知布局信任边界，当前归档符号已经额外核对。未来如扩展自定义链接布局，宜校验相关符号或限制链接脚本形态；本轮未构造真实重新链接反例，不将理论边界夸大为已复现故障。
