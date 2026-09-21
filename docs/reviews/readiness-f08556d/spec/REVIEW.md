# Readiness Spec 增量复核

准确SHA：f08556d01821d6c3c8204fdac2c38f53b2107c05。结论：限定 PASS，未发现使合同内有效预算误报条件通过的反例。

发布说明对 ca512 已获批准的覆盖明确；不将其与仍有 R1/R2 的 d3d2a3d 混合。PS桥路线、8前视/17历史、2beam+最新pending、ROM整session驻留只是A选择。启动负source_sample与真实uint64身份分层；available不早于要求状态可见、TTL映射emit显式+8。平滑回退最长960样点不取代fatal/session_abort硬停。生产状态集合、完整中间数制、profile/hash、运输和ARM映射均仍待实现或联合确认。

GOLDEN-GAPS 按软件整数、AMD、自研RTL、综合/布局布线和板级分层；旧FFT覆盖域与新S25 gate输入之间不借全域批准，portable Q30与AMD24不混作同一码golden。未发现要求重跑未受影响的FFT/录音/耐久，亦未以本包关闭 d3d 的 R1/R2。

检查器使用 Fraction，服务按各自时钟换秒再累加；队列峰值为initial+burst+ceil(rate*blackout)，在给定arrival/service包络且服务率足够条件下保守。独立 probe.py 实跑11检查通过：截止等号/多一周期、单未知时钟、26,041,666与26,041,667ns跨整数包峰值、持续率不足及5个包相位边界。结果见result.json。

非阻断限制：部分queue字段仍None时，另一个负数/bool字段未单独报schema错误，但整体queue结果None且REALTIME_BLOCKED；当前检查器不是全量schema验证器。未知burst/T/R不可据此获容量批准。

命令：
`C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -B F:/NUEC/review-evidence/readiness-f08556d/spec/probe.py`

首次临时stdin探针未指定UTF-8，在Windows默认GBK读取JSON时报UnicodeDecodeError；正式保留脚本指定UTF-8后通过，不是作者检查器错误。

限定批准A侧合同建议、golden缺项列账和条件预算检查器。所有16服务实际上界仍未知；无ARM/BSP、AMD/RTL、真实状态屏障/CDC、板卡、实时或完整H3批准。主流程官方30项/11源不在本轴重复累计。
