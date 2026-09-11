# 交付清单检查器自检

2026-09-11，PowerShell，使用 instructions/verify_delivery.ps1。

- 对固定提交69dd471的原submission执行：按预期拒绝，报告README.md不匹配及6份新日志/证据未列入清单。
- 只在包外临时副本执行作者已有update_manifest.ps1，重新生成测试副本清单；再检查：DELIVERY_MANIFEST_PASS files=39。
- 原submission与固定提交相比无差异；没有替作者修清单或改写其提交。
- 此正负测试只验证清单检查器，不产生新的Vivado/RTL验收结论。
