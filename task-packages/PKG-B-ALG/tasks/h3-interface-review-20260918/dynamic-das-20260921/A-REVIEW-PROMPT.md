请复核 task/member-b-dynamic-das-01 的准确远端 SHA（先 git rev-parse HEAD 并记录），范围为既有 H3 包的 dynamic-das-20260921 增量与父 snapshot。

基线 main fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd；b5913e5 与349501c 已由 A 限定复核合入，不重复全套旧检查。本轮不改默认算法、阈值、原 Tracker、录音或 A/C 文件。

先读本目录 README.md，按其中 run_all.py 命令运行到全新输出目录。检查源码/旧 snapshot 字节保留，整数/ROM 严格比较；生成 JSON 的环境与路径字段不同不得误判算法失败。检查日志、失败及范围，不把作者自测代作独立复核。

重点：

1. 动态 DAS 与独立 Fraction PCM 参考的分块/因果性/端点结果；不读取零权重邻点后 ±8 样点域确实只需8前视，17行历史是否够用。800次密集切向、HOLD不刷新TTL、同拍fresh与expiry的顺序。
2. 新串行切向策略最多两个活动beam和一个pending，但它不等价旧立即重定向。TTL/SEARCH/STOP后最坏960样点(20ms)完全回单麦，STOP不是硬件紧急停止。请明确该策略是否可作为下一步候选，不能不经裁决接入生产。
3. 92,160角/276,480延迟码 Decimal 60/90位参考与旧float一致，运行时ROM严格整数和SHA；完整552,960字节需明确存放处。ROM域可S16，但通用+8样点需要S17，不能混用。
4. 64项保守区间推导、原DOA AST边界、Newton分段区间与CORDIC宽度；范围界与数值误差证明分开。RNE内部余数/进位及实际除法器等未冻结，不把保守表直接当最小RTL资源。
5. 原Tracker→ROM→候选DAS是数学PCM组合验证，不是gate/DOA全流、session原子提交、声学收益或实板。只审新增部分，不重跑FFT/IFFT/run05/八段/耐久。

请回报准确版本、实跑与未测、阻断及限定批准范围。作者申请只限离线候选、验证和数制/预算增量入库，完整H3/生产profile/RTL/实时/实板不在批准范围。通过后由 A 合入，B不自审自合。
