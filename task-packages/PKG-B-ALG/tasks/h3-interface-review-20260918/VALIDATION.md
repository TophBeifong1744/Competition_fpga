# B 作者增量验证（待A独立评审）

实际日期2026-09-20，Python3.12.14 / NumPy2.3.5。没有新硬件或声学验收。

1. 从固定A分支官方API确认16afda2772b37ca5e50852c0f62944cd6f541472，重构对象并按Git SHA校验。先读REVIEW再读README；两份原件纳入inputs，出处和原字节SHA在references。普通Git fetch首次连接重置，API成功，不伪称fetch成功。
2. 在新分支独立工作区运行 `source/framing_review.py --out F:/NUEC/review-evidence/h3-review-package-20260920/generate-run01`：8组合成会话/区间＋S1共9组，6类非法输入拒绝；生成golden/framing.json、synthetic-frames.npz、budget.json。未改变上游源文件。
3. 封存初稿15项清单后，运行README单命令到包外reproduce-run01：27项引用前/后校验通过；9组新golden与冻结值一致；S1 561帧/506尾样点；5项冻结证据篡改（row_start、原始ID、slot序列、PCM值、预算）均被比较器拒绝。原始命令/cwd/环境及结果见evidence/author-run01.json。
4. 随后仅追加本验证说明、发布入口及原始运行记录，初稿清单保存为evidence/initial-seal.json，最终PACKAGE-SHA256重新封存本包。最终清单/27项引用再做只读检查；不重复未变化的分帧计算，更不重跑旧FFT/耐久。本包不是“15项”最终文件集合，以最终清单为准。

覆盖：四路可区分PCM、ID大于2^53仍精确、逻辑区间1023/1024/2048边界、3000组跨250包双槽、clip1250切段、丢号1500标记错误行、不同session重启不能拼接、S1真实记录完整帧索引。6类拒绝为reserved、非法flags、signed24越界、截断、重复ID、倒序ID。

所有尾部均保留在输入，只不构成FFT帧；合成逻辑区间的最后不足250组切片明确不代表硬件接受短DMA包。双槽回放用覆盖旧槽后校验独立副本证明复制/索引逻辑，不模拟真实DMA时间、缓存一致性、队列背压或并发所有权。

未重新执行：前向FFT覆盖、IFFT仿真、run05的39项/14数组/音频50项、S1导出17项、E1耐久、RTL/CDC、ARM构建、综合实现、下载/上板。其准确旧证据/批准由references固定；不得把引用计为本次新执行。

没有完整H3 PASS。尤其没有生产最终数制冻结、已验证无目标门、完整模块WCET或实时输出。请求A仅评审本次集中合同/分帧golden及最小准入边界。
