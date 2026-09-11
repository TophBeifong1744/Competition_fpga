# mic-wiring-draft-0.1 文件与输入清单

日期：2026-09-09。全部路径相对仓库根目录，哈希算法 SHA-256。批准状态：待 B BryanZheng802 复核；未合入。批准范围不能由哈希一致自行推定。

## 待审交付

| 文件 | bytes | SHA-256 |
|---|---:|---|
| task-packages/PKG-A-ACQ/payload/hardware/microphone-wiring-candidate.md | 11600 | 6436395e80308c4126f07b72a04bedd08b2c43a6b6a64da8a91c52ae5c724d6b |

动作：新增候选，未来目标 hardware/microphone-wiring-candidate.md；当前目标未写入。包内 README.md、REVIEW.md、manifest.md 仅追加本增量入口/待复核状态，不改 H1 历史哈希或 DDR 冻结证据。资料核验 README 是作者自检记录，不是人类批准；本清单不自哈希。批准文档版本以此 payload 哈希为准，记录性文件如需一并批准，由复核人对当次完整差异另行绑定提交或清单。

## 只读公共输入

| 文件 | bytes | SHA-256 |
|---|---:|---|
| hardware/reference/navigator-zynq/navigator-zynq-baseboard-schematic-v3.9.pdf | 2361991 | ec8b68eeb07e0743e6c60528444f6aeb457dc60e897ddf9eb86d5a56c1ab6a69 |
| hardware/reference/navigator-zynq/zynq7010-7020-coreboard-schematic-v2.5.pdf | 2430251 | 1c8cf8105e91d762d29ad604e82b629b3921fa474d5a0311ed6c04237db107ea |
| hardware/reference/navigator-zynq/navigator-zynq-board-spec-v1.2.pdf | 4107906 | b974ed61b10fabafe408a42d119e94fc53c6133a9a7fc64b0191bfe5e14744e6 |
| hardware/reference/navigator-zynq/navigator-zynq-io-pin-map.xlsx | 20248 | 287a73b93b9a5a4a05e2145b92338c37717e033dced64db502510ba0cfac7093 |
| hardware/reference/navigator-zynq/navigator-zynq-io-reference.xdc | 9204 | 6803fab6ed43af125293b9fb8434e6fd4b7c0b8a38c09719d51f3b829b54de71 |
| hardware/reference/infineon/im73d122v01-datasheet-v1.00.pdf | 869439 | 1a597dbd8ff794b98d09a8b214eb1f9e864f36ae4a05d4eaf0d9c3ba6211ce36 |
| hardware/evidence/microphone-c-2026-09-09/README.md | 4045 | 3770ee2c261522884c8bbeab9d0efd507aedd4f104823222e0808bb325b845d3 |
| hardware/evidence/microphone-c-2026-09-09/image/引脚分配.jpg | 203361 | 90ff6bdcd4fdfaf5e5c425319f346223fe31d246a8af20061ae1c479dc5f22e5 |

原件只引用，不复制、改写或重签。资料来源有效不等于实物核验完成；原理图/规格书仍需与实际核心板装配和电压逐项对应。
