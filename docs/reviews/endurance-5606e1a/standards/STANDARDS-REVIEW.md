# E1 规范／串口证据轴

准确提交：5606e1a9d9a6183ceff7cffc1bb4f8aac44bb79c；父提交ad9ca72388fb676946c71b13517ab279c11cfc61。依据AGENTS.md、CONTRIBUTING.md、docs/team-workflow.md，以及publication/README.md的限定归档申请。作者原件只读，未运行硬件或重复主审23项及C模型。

## 结论

本轴没有阻止固定E1源码／构建／实板记录限定归档的硬规范违规。按用户授权保留的完整原始证据和构建快照不机械套用一般生成物禁入规则。旧bbe39检查器及未继承启动／封存保护的局限已明确，不能据此把本次归档描述为安全构建／加载工具批准。

独立固定UART审计通过：11段、44通道、19,202,750组、76,811包、614,488,000字节；逐段编号跨度、计数、停止／排空、两槽终态及最后16包轮转一致。独立增加成功末游标249/3、末mic3值的signed24范围及与该通道min/max相容、零值计数与极值相容检查，原日志全部满足。原始日志SHA-256与冻结值相同。

`continuous_core.c:83-111`的正常所有权转移保持DMA_OWNED→CPU_READY→CPU_OWNED→FREE，检查完整包及guard后才释放；`:116-120`返回成功前要求停止排空、无活动槽、双槽FREE及DMA idle。`main_continuous.c:84`初始化在段循环之前；`:94-102`正常段间仅采集、排空、打印与等待；`:115`的DMA reset位于失败路径。`normal_between_session_resets=0`是源码输出的固定声明，结合OPERATOR-CONFIRMATION.md支持“成功段间无人工复位”，不是独立电源／外部复位测量。初始GUI Run含初始化／复位，最新发布说明明确如此。

两次真实post拒绝均保留`Object timer code differs from fixed computation`；早期pre拒绝是旧候选源码。后续布局修复、事后复查和20:52新编译按时间分别记录，未将事后复查冒称新编译。原IDE控制台仅尾段，归档未宣称完整。实板没有PCM全量留存，不能重新离线逐样本验证；未扩写为连续400秒、一小时或M1/H3通过。

## 非阻断维护观察

`board-run-20260916-01/verify_log.py:55,65-66`只校验独立数值范围，遗漏成功游标、最后值与通道统计之间的关联。独立变异将bad_group改0、bad_value改7FFFFFFF、mic0改min=1/max=2/zeros=1，均仍返回UART_EVIDENCE_CONSISTENT_NOT_ACCEPTANCE。owner非FREE与drain达到2秒则拒绝。建议以后复用此解析器时补交叉字段约束；这些反例不在固定日志内，本次独立审计已补核，故不阻断本次限定归档，也不把解析器批准为未来日志的完整语义验收器。

这属于实质维护覆盖缺口，不因启发式气味单独升格硬违规。其余命名、重复、职责、成组数据及类型使用未发现值得单列的问题。

证据：`independent-uart-result.json`；复现源码`independent_uart_audit.py`。均仅位于包外F:/NUEC/review-evidence/endurance-5606e1a/standards。作者工作树git status保持空。
