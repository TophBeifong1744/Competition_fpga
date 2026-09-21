请修复PSB-B-01～03；准确基线fbbaa161098582ba1e5e112b86d39533769bb3e7，完整反例和合同判据见B-REVIEW.md及spec/、standards/。

1. 整批预检/聚合完成后才commit，payload或binding冲突任意排列都不得产生可消费结果；检查实际commit/take，不仅返回码。
2. 当前session未知事务error（含越界slot）按合同fail-stop，保持旧session隔离。
3. 最大generation选择/保留规则一致，不发布不可acquire的READY帧。

保留原代码、旧清单和失败证据，修复交准确新SHA；明确原33项和新增反例、源码与依赖绑定。旧0ab与新a7合同对照分别标注，不静默换原引用。
本轮不要求上板、ARM/BSP、旧FFT/录音/耐久重跑；ASan/UBSan仍按实际工具可用性报告。候选尚未合main，B反馈不批准生产ABI、Vitis、实时或完整H3。
