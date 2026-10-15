# I14-TOKEN-01-PUBLISH：准确候选来源

本目录将已限定接受的两份主机 C 候选源文件接入既有 `ps-semantic-bridge-repair-01/src/`，供固定提交和 Draft PR 核对。产品源文件由 2026-09-30 候选原字节复制，未在发布批修改；父版提交为 `f8367f5bd2bd7d52348c9259a9051ff050c4f1ab`。本目录不替代原作者包、独立技术复核或真实成员决定。

既有 `repair-01/README.md` 的 PENDING 叙述、旧 `SHA256.json`／封闭清单和历史证据保留原字节，描述其旧版本。若旧 `manifest.py` 或 seal 校验绑定旧 `src/`，应在准确父提交核旧包；不能将本次已替换的 `src/` 送入历史全包门禁后宣称旧清单仍覆盖当前源。当前两源的独立身份以本目录 `SOURCE-BINDING.json` 为准，既有批准范围不扩大。

| 对象 | SHA256 | 可读入口 |
| --- | --- | --- |
| `src/ps_bridge.c` | `bac5f31018a9edb87d4bc64321dce15da5d266f6e82a92abf86125a69de2e0d2` | `SOURCE-BINDING.json` |
| `src/ps_bridge.h` | `e7e68fd0367fd0a8623c635cfdd3d870df334bfbaf76741c60b98667c80d4124` | `SOURCE-BINDING.json` |
| 两源集合 | `a97c9493d02bc26655bd8c05f68aaaf08d40e0eff950253f99c1c2976f2f34b5` | `SOURCE-BINDING.json` 内重算规则 |
| 原作者 `MANIFEST.json` | `00a419123874b45dd7b18d854789aaf38c2d6f800fd523f4d27db88cfb97b61d` | 下列原件 ZIP 的 `inputs/codex_out/i14-token-current-malformed-implementation-20260930/MANIFEST.json` |

原件可从 [B 的可携复核包](https://github.com/TophBeifong1744/Competition_fpga/releases/download/b-evidence-space-trial-20261002/i14-token-b-review.zip) 读取，ZIP SHA256 为 `6fb834ac5b624fdedfbbe9a50e5be0d3906cb63036b9bc1b30a0581c9acda6f3`（872994 字节）。其中 `inputs/codex_out/i14-token-current-malformed-implementation-20260930/` 保存原两源、MANIFEST、`PRODUCT-FREEZE.json`、最终 `runs/20260930T131908Z-1848f020/` 及失败快照。另有 [B 复核报告](https://github.com/TophBeifong1744/Competition_fpga/releases/download/b-evidence-space-trial-20261002/i14-token-REVIEW.md)（SHA256 `d1a7c6e25f3848f380c25001e96bcd47160b56ed1e1940a32f556c43290bf387`）和 [证据索引](https://github.com/TophBeifong1744/Competition_fpga/releases/download/b-evidence-space-trial-20261002/i14-token-evidence-index.json)（SHA256 `25ba7010a3fc0d637ecf3e9a94edcee399ba02072d32ae91829463d5eb7cb47d`）。本仓库本地原件入口为 `codex_out/i14-token-current-malformed-implementation-20260930/`；原 R 技术报告为 `codex_out/i14-token-review-a97c949-20260930/REVIEW.md`，SHA256 `27551c907ba0b7fb31cd7729ec383f334d9ee882fe782e3ca6af497b914acc6d`。

[M 派单和 B 本人限定确认](https://chatgpt.com/space/page_046d52c0ffd481918d86cfb5b70d7a09) 的准确 block 身份见 `SOURCE-BINDING.json`。B 本人确认对应这组未提交两源及原 MANIFEST；技术报告单独不能充当成员批准。提交后的完整 SHA 应由包含本目录的 Git 提交、Draft PR 与外部发布回执绑定，不预写到提交自身文稿。范围和证据限制见 `CLAIM-SCOPE.md`。
