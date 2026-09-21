# 失败、反例与未运行记录

- 初始在共享develop读取不到最新复核路径：该目录HEAD是f364a02旧任务分支，不是最新main。未切换/重置/清理它；转为独立短路径 `F:/NUEC/r/h3e`。
- 首次长路径worktree创建因A深层历史文件超过Windows路径限制失败，Git撤销了该worktree登记；没有删用户文件。随后以短路径和单命令`-c core.longpaths=true`创建成功，不改全局配置。
- GitHub fetch多次报443连接失败；一次ls-remote成功发现更晚main。提升身份在新worktree读取Git遇dubious ownership，未设全局safe.directory；网络操作改从用户指定develop进行。最终刷新身份见DELIVERY，不把早期缓存称最新。
- 默认python为3.7.0/NumPy1.21.6，实际运行全部用Codex Python3.12.14/NumPy2.3.5；没有用旧解释器执行后再隐藏失败。
- `original-cordic-counterexamples.json`保留942个旧函数误差>1 Q8码的确定性反例。新候选仅增加共同左移与规范角度，未改旧函数；此为通用输入域缺口，不是旧DOA门内声学失败证据。
- 14类轨迹反例是预期拒绝，原输入与首错原因存于最终`checks/expected-rejections.json`及同名JSON。没有删错例、放宽断言或用日志中PASS数量代替返回码。
- run01为初始软件探针（12类轨迹错误）；run02增加独立Fraction PCM、外部状态集合防弱化和预算运行；run03加入CORDIC保守宽度递推。均保留，最终复现以run05和源码哈希为准，不累计重复测试。
- 未运行：新AMD C/RTL全链、Vivado/Vitis工程、RTL时钟背压/CDC、PS C、综合实现、板测、完整声学研究。旧已批准测试本轮未重跑。
- 最后静态检查发现同拍事件数组顺序可能使commit先于error，未发布前修正为submit→status/error→commit的优先顺序；run04新增第14类反例通过。run05为最终固定源码运行，之前输出不重写、不累计。
