# WP-S1 文件清单

版本：2026-09-08-r1。机器可读清单：[evidence/files.json](evidence/files.json)。批准时须绑定该清单 SHA-256 或整个提交及批准范围。

3 份 payload；0 份只读引用。所有项目均为待复核，合入动作尚未授权。本次无删除、无自动覆盖总工程。

| 待审文件 | 总工程目标路径 | 包内 SHA-256 |
|---|---|---|
| [skill/soundsight-engineering-workflow/README.md](payload/skill/soundsight-engineering-workflow/README.md) | `skill/soundsight-engineering-workflow/README.md` | `a80d51ae90d7978e549522f2cde52344cceceabf02a933135c947283594e2d41` |
| [skill/soundsight-engineering-workflow/references/record-templates.md](payload/skill/soundsight-engineering-workflow/references/record-templates.md) | `skill/soundsight-engineering-workflow/references/record-templates.md` | `79e724554605dd97565f32bc68709554ac188f55755e2e965b3d0c0fa75c61a2` |
| [skill/soundsight-engineering-workflow/SKILL.md](payload/skill/soundsight-engineering-workflow/SKILL.md) | `skill/soundsight-engineering-workflow/SKILL.md` | `2c2d71d43ca18b038c320649c502f5272146ae3c5841738cc7c8896ff8092271` |

## 只读引用

原路径、大小与采集时 SHA-256 全部保存在 files.json 的 references 中。既有冻结原件不迁移、不重新签名；references 的 snapshot_path 指向包内原始字节只读副本。引用发生改变时先查来源；当前清单不取代原始冻结清单。

源工作区 HEAD：`e21247b0a6f55efd2fc1095c6e65cac6ac259162`，含未提交修改；推送基线为 `f0f397f5600f111df5c66dafa34090b260ad6e00`。两者不同，不把任务分支声称为主分支最新状态。
