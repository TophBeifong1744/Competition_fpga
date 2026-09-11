# C-RTL-004-R2：只整理最终交付，不再改RTL或重跑

日期2026-09-11。本批仅此一项，仍属004，不新发005。适用基线69dd471；独立复核已通过含空格路径BD恢复，原功能228次核对仍有效。

## 要完成什么

关闭1个交付问题：README与清单不同步，新增6份成功证据漏列。不要重写代码、重跑仿真/BD、补截图或启动板测。

## 按这个顺序做

1. 在既有C分支更新到本操作单的提交，所有成果继续在C-RTL-004/submission。不要合并main。
2. 原样复制当前file-manifest.json到 evidence-history/manifest-before-rework-02.json；其SHA-256应为d672c884b92b5a35c346c62480c3fa18bde81c0c3a9b6ebf0092bf13ac502613。如已存在先核对一致，不覆盖不同历史文件。
3. 修改submission/README.md：当前状态写“功能及含空格路径BD独立技术复核通过，待完整交付核验和B正式批准”，引用 ../review/69dd471-20260911/README.md。版本更新为1.1-R2。保留历史失败过程，并将过时的“R1验证未完成”明确标成当时状态。不要把复核方含空格路径成功写成作者亲自运行的结果。
4. 明确新作者成功证据位于 logs/rework_01_20260911_194059/，旧 logs/rework-01/ 是先前失败记录。只需在当前README解释；原始日志、旧阶段报告及旧失败说明不要改。去掉当前操作说明中已经过期的“不推送远端”，改为本分支发布、B批准前不合main。
5. 完成所有文件修改后，最后运行已有脚本更新当前清单：

```powershell
# 当前目录为 C-RTL-004/submission
& ./scripts/update_manifest.ps1
& ../instructions/verify_delivery.ps1 -SubmissionDirectory .
```

6. 检查脚本必须打印DELIVERY_MANIFEST_PASS，不能有遗漏文件、重复路径、字节数或哈希不一致。成功后不要再改清单涵盖的任何文件；若有变更，重新执行第5步。清单检查脚本本身只读，不启动Vivado。
7. 仅提交本次README、历史清单备份和更新后的file-manifest.json，再推送既有 codex/c-rtl-001-outsourcing-docs；向复核方提供精确提交号和检查结果。不要要求C先做新一轮仿真。

## 验收与边界

复核人确认源码/脚本未变、历史证据未动、当前清单覆盖完整且全匹配后，关闭本项。若只发生上述文档/清单变更，沿用既有功能与BD独立PASS，不循环重测。B正式复核及主流程活动目录集成仍按原职责执行。
