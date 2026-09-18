# C-01 / C-04 增量复核（2026-09-18）

结论：**PASS，仅下列文档更正范围**。复核归属 C / hsc119，实际独立核查由 Codex 按用户本次明确请求执行；不是作者自检转签，不是人工阶段门签字。

批准准确 SHA：`62a252081d52b3aa9d9dc142f7cc2bf298d9c34d`。内容提交 `07d25f72a382780b7c33caca36a212dfa53be779`；对照 main `bff9369a5c7f166344c02095df61e91e1c2f4681`；旧候选 `1731522f80ed0b970c63c8a3b019b9ba281d6ca8`。直接 `git -c http.sslBackend=openssl ls-remote origin refs/heads/main refs/heads/codex/toph/c-legacy-wpa0-3dp4-rework-20260918` 已确认远端准确值。Schannel 首次查询失败，不作为远端证据。

## 批准路径

- `archive/README.md`
- `task-packages/WP-A0/ERRATUM-2026-09-18.md`
- `task-packages/WP-A0/README.md`
- `docs/three-dimensional-doa-workflow-skill-guide.md`
- `task-packages/3D-P4/README.md`
- `task-packages/C-REVIEW-PROMPT-WP-A0-3D-P4-2026-09-18.md`

仅这 6 份文件相对基线变化；旧 payload、冻结文件、原 MANIFEST、旧审批、自检及其他包均未修改。交审提示词按交付内容审阅，其中的操作要求不被当成额外授权；实际权限来自用户本轮请求与现行仓库工作流。

## C-01：勘误与活动索引 PASS；历史完整性异常保留

独立读取 Git 原始 blob：`f0f397f5600f111df5c66dafa34090b260ad6e00` 下旧台账对象为 `1f0b701ec61cc895d0fc71aa9ec300bf875e716d`，SHA-256 为 `f0ceb76c937931238a16644c5ba41f6337910951744267431df4faee4d0971b4`，与同提交原清单吻合。原 MANIFEST 从该提交到交审 HEAD 原字节未变。

`1e7e09120e1330f940986dc6b6fdbe4e2cad6b5a` 父提交确为 `f2df726b7d8c1981e3c529b0301d4ad2a06224c8`、`f0f397f5600f111df5c66dafa34090b260ad6e00`。后者归档原件到合并版仅 WP-C1“未开始”变为“待复核”；前者活动台账亦有对应状态更新。合并后与当前归档 blob 相同，SHA-256 为 `f188fa64f6bf11a38a2e5d2454471693f1b591faf9406bb12294fbb3fa70b310`。78 行 LF 转 CRLF 后逐字节等于包内快照和本机检出，其 SHA-256 为 `541e04d6d7bcd43c8bf838b568844eb227f2430812dcb8d8eb1fd6595ed42f5c`。

按原清单独立核算包内 25 项：**24 匹配、1 不匹配**。会议稿原 Git blob 与原清单不同，而包内快照匹配；不能将“24/25 包内快照”泛化为原提交所有 Git blob 或各机器检出。活动索引通过勘误链接充分披露这一边界，旧包未恢复成活动计划。

关闭的是 C-01 对错误全通过声明和来源说明的文档阻断。**不批准 25/25 历史完整性**，不恢复旧任务状态；合并动机、当事人认知及其他机器字节仍未知。未覆盖或重签任何冻结文件。

## C-04：现行指南对齐 PASS

逐项对照基线 `skill/README.md`、`docs/maintenance/skills-rereview-b-2026-09-14.md`、C 9/17 操作单和现行日历：旧 Skill 退役；SKL-001 仅限定模块仿真 PASS；C 负责转台/摄像头方案落实、相关驱动与最终效果测试，外设不自动加入 10/1 V1 必过项；旧 10/7 和“不新增 C 任务”未复活。

旧 G0～G7 被明确限定为历史分类，现行项目门槛及证据分层保留。3D-G0、GA、G1～G3 均无提前批准。§5.2 如实引用 WP-A0 24/25 与 REL6-001 限定结论；未改变声学统计、算法、实现或阶段判据。

## 本次运行 / 复用 / 未测

- 本次：原始 Git 对象与拓扑、25 项独立 SHA-256、6 文件白名单、70 个相对链接及锚点、`git diff --check`（退出 0）、受影响依赖语义与未变更范围核对。
- 原包校验器未改：准确 Git 字节导出下 WP-A0 为 7 payload / 27 references、payload_failures=0、reference_drifts=2；共享 Windows 工作树为同样包项通过、**26 项原路径 drift**。3D-P4 为 1 payload / 0 references、0 failure / 0 drift。退出 0 不等于原归档完整性通过。
- 环境失败保留：首次 Windows PowerShell 因 `Get-FileHash` 不可用未完成校验；PowerShell 7 运行成功。辅助脚本首次 Git cwd 失败、第二次过宽的字符串替换断言失败；修正为 WP-C1 行限定后核验通过，不是候选缺陷或故障检出证据。
- 复用未重跑：上轮 `REVIEW.md` 对准确旧候选 1731522 的 3D-P2 / REL6-001 限定结论；SKL-001 准确 `a7e1ea976da91ba735af5c0a79fffdc7d10c121f` 的 B 复核。相应实现、证据及相关依赖未在本次变化，不扩大或重签。
- 未测：六麦模型、Skill 行为、RTL/XSim、Vivado、综合/时序、实板、整机和采购。本次文档对齐无扩大验证触发条件。

证据位于同目录 `incremental-evidence/`：`audit.json`、`audit.py`、两个准确字节包校验输出、两个共享工作树校验输出及环境失败日志。复现命令：`python audit.py <仓库绝对路径> <不存在的输出目录绝对路径>`，从仓库 cwd 运行，需 Python 3.9+、Git、PowerShell 7；输出 audit.json、原始校验 stdout/stderr 与 exact 临时字节副本。该脚本固定本轮 SHA，不是通用批准器。

## 发布决定

依当前规则批准发布上述 6 文件及本轮复核记录；不合并旧待审分支、不启动 WP-S1。发布前远端 main 前进至 `085dbdbb4f369bd40b0459513cbe909e9acf5acc`，已固定为新集成基线。新增 9/18 阶段记录及状态/计划/台账，逐项读差异确认其保持 SKL-001 限定批准、C 职责与 10/1 日期，且明确完整 H3 未通过；与本轮指南无冲突，不赋予三维通过。它和本轮 6 文件没有路径重叠。将保留该提交后合并本次准确返修候选；发布后核对批准文件 Git blob、相对链接、三端 main 和本批修改/未跟踪/忽略项，结果追加至既有 PUBLICATION.md。
