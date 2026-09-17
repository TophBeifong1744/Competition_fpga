# 两项 Skill 9/18 增量范围检查

执行2026-09-17六项增量复核规则：两项活动目录自批准版本无变化，因此不重复全量测试；只核对准确SHA包含关系、路径差异、入口哈希、已批准案例和当前未测边界。当前机器结果见 `evidence/run03/skill-scope.json`。

## SKL-001

- 准确批准SHA：`a7e1ea976da91ba735af5c0a79fffdc7d10c121f`；当前HEAD包含它，活动目录差异为0。
- 输入/输出：模块合同 + RTL/TB/case → XSim阶段日志、首错、修复后检查与结果；不输出生产RTL批准。
- 已有基线/正常案例：PCM符号扩展、elastic ready/valid正常与复位恢复。
- 已有失败边界：bad data、bad ready、两级延迟、满槽容量、X/Z。
- 未知故障证据：历史独立signed8饱和加法故障可复用；本轮未改相关输入。
- 迁移/陌生案例：9/18没有执行新的工具版本迁移或新陌生模块，`NOT_RUN`；这不阻塞当前限定Skill保持有效，但不能宣称9/23最终案例完成。
- 结论保持“模块仿真限定通过”，不写生产RTL、综合、时序或板测通过。

## SKL-002

- 准确批准SHA：`3ac597d1d16982e0a5c5a114202ca8568dc28d8f`；当前HEAD包含它，活动目录差异为0。
- 输入/输出：profile/session/golden → static/mock报告、错误、缓存/所有权轨迹；真实硬件入口受保护。
- 两套配置：thermal signed16/96-byte与pixel uint32/128-byte合成profile，均为离线复用证据，不是第二块实板。
- 失败案例：缓存陈旧、timeout/abort-timeout、短输出、重复ID、release失败、大整数 `2**120` 一码差；原B复核为55方法/57 subtest及14会话。
- 真实 PYNQ、Overlay下载、物理DMA、吞吐、资源/时序全部 `NOT_RUN`；比赛加分风险仍开放。

本页不是新的独立技术批准，只确认已批准范围在当前主线未漂移，并把未完成案例带到后续日历。
