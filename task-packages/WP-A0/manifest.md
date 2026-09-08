# WP-A0 文件清单

版本：2026-09-08-r1。机器可读清单：[evidence/files.json](evidence/files.json)。批准时须绑定该清单 SHA-256 或整个提交及批准范围。

7 份 payload；27 份只读引用。所有项目均为待复核，合入动作尚未授权。本次无删除、无自动覆盖总工程。

| 待审文件 | 总工程目标路径 | 包内 SHA-256 |
|---|---|---|
| [archive/README.md](payload/archive/README.md) | `archive/README.md` | `4066dda96cc03e1f63f414f68c74974fcfab8d2f03777f95367f17a2b2591e46` |
| [docs/current-status.md](payload/docs/current-status.md) | `docs/current-status.md` | `e94158a2fe549c35a803fe8f069118fca34ae4eaca68e98147085521b3b965cf` |
| [docs/project-plan.md](payload/docs/project-plan.md) | `docs/project-plan.md` | `837e94176d835f0bada83d1ef9b15720d584e5854c6c3b5a5ec8b5241c406058` |
| [docs/README.md](payload/docs/README.md) | `docs/README.md` | `16e506832365bca78e95ff6430104ea1658dc1582e9c1a037b33b2b6739e2334` |
| [docs/team-tasks.md](payload/docs/team-tasks.md) | `docs/team-tasks.md` | `dc62a72dc021015b118550939d03ce349c2ee1744d1349066ebb38eca739b496` |
| [docs/work-packages.md](payload/docs/work-packages.md) | `docs/work-packages.md` | `d982d72c4b2894173f300960c490bc8cab623a7b3a0d999ba0060c03b7a01f4e` |
| [README.md](payload/README.md) | `README.md` | `3c5d3b78fe94a4baeef4e12eecfbcaaae48500040ac124b5c7f908917a8e1c8b` |

## 只读引用

原路径、大小与采集时 SHA-256 全部保存在 files.json 的 references 中。既有冻结原件不迁移、不重新签名；references 的 snapshot_path 指向包内原始字节只读副本。引用发生改变时先查来源；当前清单不取代原始冻结清单。

源工作区 HEAD：`e21247b0a6f55efd2fc1095c6e65cac6ac259162`，含未提交修改；推送基线为 `f0f397f5600f111df5c66dafa34090b260ad6e00`。两者不同，不把任务分支声称为主分支最新状态。
