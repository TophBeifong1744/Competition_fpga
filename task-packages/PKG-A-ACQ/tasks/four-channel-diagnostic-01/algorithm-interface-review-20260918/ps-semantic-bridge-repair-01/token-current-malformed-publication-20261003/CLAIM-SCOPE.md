# 本次发布的限定结论

本批只把准确两源集合 `a97c9493d02bc26655bd8c05f68aaaf08d40e0eff950253f99c1c2976f2f34b5` 从原候选按字节接入既有主机 C 包，并公开来源入口。原 R 技术结论为 `PASS_WITH_SCOPE`；B／BryanZheng802 本人在 [原任务页](https://chatgpt.com/space/page_046d52c0ffd481918d86cfb5b70d7a09) 对该两源及作者 MANIFEST 作限定确认。本次发布是来源绑定，不新增功能验证或工程准入结论；整个 I14-TOKEN-01/#14 仍 OPEN。

获接受的子范围：入口时 `active && !failed`、当前 session、`error=false` 时，越界 slot、generation 不符及 FREE 槽三类畸形 token 的主机 C fail-stop；新增 reason `65536`、kind `9`，整批新 commit 抑制、故障锁存，以及审计队列已满后 `last_event` 对原畸形 token 的优先级。历史已发生的 take/物理消费不声称回滚。

证据沿用原包最终 `runs/20260930T131908Z-1848f020/`：O0/O2 各 24 个功能 case 和 3 个检查谓词 canary；57 是版本、编译及 case 的子命令数，不是 57 项独立功能。canary 只证明指定谓词输入被拒绝，不是 DUT 端到端变异。原顶层 runner 独立原生退出字段缺失；保留 v1 缺成功标记、v2 断言首错与最终记录。原冻结/运行清单中的 `FUNCTIONAL_SIM` 历史标签只按主机 C 事实解读，不能据此签 RTL FUNCTIONAL_SIM。

以下仍为 OPEN、NOT RUN 或 UNVERIFIED：未知 boot、future/noncurrent session 的可信归属及旧回调映射、更广 inactive 审计、生产 ABI 与旧消费者、并发/ISR/重入、真实时基与实时性、ARM/BSP/Vitis、DMA、RTL/CDC/RDC/STA、板测及物理消费回滚。未在本发布批运行功能测试、编译、EDA 或板测；旧证据只在上述准确源身份和限定前提下复用。若源字节或范围变化，须按影响重新复核。
