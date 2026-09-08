# PKG-A-ACQ · H1 候选文件清单

当前状态：H1 的 7 个 payload 文件已由 B 审核并随 `be74e0a` 合入目标路径；DDR 增量仍待复核，完整包未通过。H1 原始文件清单与哈希不变，审核依据见 [REVIEW.md](REVIEW.md)。

## DDR 五模式自检增量（2026-09-08）

新增 payload/ps/ddr_test/src/ 与 evidence/ddr-five-pattern-v1/，准确文件/原始来源哈希见 [DDR 清单](evidence/ddr-five-pattern-v1/files.json)。源码文本副本仅规范换行/文件末尾空白；二进制与初始化文件保持原始字节。原 F 盘工程未修改；无删除、无自动覆盖总工程。该子项待 B 复核，完整包继续进行。

XSA 内的 bitstream 和 ps7_init.tcl 与独立归档文件哈希核对结果记录在 DDR 清单中。H1 旧版本清单保持不变，以下为原 H1 交付时的历史记录，其中“活动文件保持不变”“尚未授权”仅描述当时状态，不覆盖上方已合入结论。

版本：ss-data-draft-0.3；状态：候选自检通过、A/B 确认待完成。只列本轮输入与文件，不代表完整采集包完成。

源 HEAD：e145b0c6f3d50136b5963db89fc75838c2fb5aff；活动 docs/minimal-data-interface.md 原始 SHA-256：f35b169813235e57dc20b2b5c194ce84270ffcb23cf3943b906b3e3b63579db5。活动文件保持不变。

| 包内文件 | SHA-256 |
|---|---|
| [payload/docs/minimal-data-interface.md](payload/docs/minimal-data-interface.md) | `5489c6945230d338e3836c8a5d3007ddaf2257190b4cad016615569ae2d0ca00` |
| [payload/examples/h1/code-pattern/metadata.json](payload/examples/h1/code-pattern/metadata.json) | `2f1aca137563cdecb72a59c87f73a20233e62ffcd4e9997a798dc3ee5df93964` |
| [payload/examples/h1/code-pattern/samples.csv](payload/examples/h1/code-pattern/samples.csv) | `c02fdf3855e87a2d8c6e57ebbeb2b9304ab00cd7cd5c9afe022bad00574b9d0f` |
| [payload/examples/h1/reader-test-plan.json](payload/examples/h1/reader-test-plan.json) | `2a3de3dc33e0b500d62ffd97207b2f262b35e9a4c1c823b82985b793b7fd8afb` |
| [payload/examples/h1/restart/metadata.json](payload/examples/h1/restart/metadata.json) | `c3ffc03e41ca5c8e9cee4dd050c51bcbd98d112dce299683c3b4873d019af9e3` |
| [payload/examples/h1/restart/samples.csv](payload/examples/h1/restart/samples.csv) | `d95c743494822c2279647a770fceb8bbc4d4c222d1917c9c92a77ea2e2a15119` |
| [payload/scripts/check_h1_fixtures.py](payload/scripts/check_h1_fixtures.py) | `c643072257ab008f05c56dc85f83e2b420993229bdc259d868a39381e74c8923` |

payload/ 后的路径为未来总工程目标相对路径；合入动作尚未授权，无删除。准确机器清单见 evidence/h1-files.json。双方确认应绑定该 JSON 的 SHA-256。候选修改后重新更新清单并通知对方，不静默解释旧版本。
