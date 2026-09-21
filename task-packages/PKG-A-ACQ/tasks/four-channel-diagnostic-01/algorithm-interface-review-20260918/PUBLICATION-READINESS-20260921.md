# A合同决定与预算子包发布回执

入口：[PRODUCTION-READINESS-20260921.md](PRODUCTION-READINESS-20260921.md)。分支`codex/toph/h3-production-readiness-20260921`，准确提交以本页所属发布提交及工作执行回报为准，不把基线当交付SHA。未合入main，不代签B。

## 实际完成

- 三份决定/缺项文档、机器可读16服务预算和可执行检查；初稿run01、最终run02均保留，不累加为60项。
- run02：30项检查通过，11份准确Git源绑定；最终五份源码/配置/文档哈希见该目录source-sha256.json。
- 独立工作树从main `cf026cf29518488f8c7275b825f3487a8d892f80`建立，仅复制本轮新增文件；未复制其他未跟踪任务。
- 第一次独立复跑因实际账户与CodexSandboxOffline的Git所有权检查被拒绝，返回128，FAILURE.json及命令保留于`evidence/readiness-20260921-clean-failed01/`。不是算法测试失败，不修改全局safe.directory。
- 获权限执行同一检查器后，独立副本复跑30项/11源通过，见`evidence/readiness-20260921-clean02/`。与run02预算、测试及来源语义一致；命令路径不同不强求整份JSON字节相同。
- 旧FFT、C33/122、B节点/八段/耐久不重跑。没有AMD、ARM、RTL、构建、上板、数值默认或实际one/Vitis改动。
- 发布预检仅29个新增文件；暂存Git blob与工作文件原字节一致，三份OUTPUT清单18项哈希通过，run02与clean02的预算/测试/来源/源码哈希语义相同。默认`git diff --check`将保留CRLF的JSON误报为行尾空白；原件不重写，单命令`git -c core.whitespace=cr-at-eol diff --cached --check`通过，未修改全局配置。

本轮完整列账已交；生产ABI与硬件上界未冻结，REALTIME_BLOCKED。B d3d2a3d的R1/R2、A ca512a8的独立复核各沿原任务，不由本包关闭。阶段/H3状态不改。

## 给B的集中复核范围

1. A选择PS语义桥、8前视/17历史、2beam+最新pending、PS DDR ROM及硬停/平滑回退分离，是否与准确合同一致；不把A建议当双方签字。
2. 严格状态可见时间、uint64身份/负startup例外、required_status集合待定是否清楚；旧0ab/newa7/ca512/d3d来源不混用。
3. 预算量纲、250组包相位、条件队列包络及缺项阻断正确；30项自检是检查器行为，不是实测服务上界。
4. 复用与新验证、软件与AMD/RTL、9/18列账与后续实施分层；不重复派旧测试，不新增录音/M1/Skill/C任务。

按入口命令输出到新目录，给出限定批准或具体返修。通过前不合入main。共享本轮新增原件保留为待审发布副本，其他任务未提交文件保留；尚非main批次收尾，不宣称全仓干净，不删工作树。
