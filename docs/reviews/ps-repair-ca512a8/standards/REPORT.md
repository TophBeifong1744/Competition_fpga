# Standards 轴增量复核

准确 SHA：ca512a8be7978ab6ca2ade3d5e0b922e53a89c79；基线 fbbaa161098582ba1e5e112b86d39533769bb3e7。限定 PASS，无本轴阻断。

实际运行 audit.py：仅修复目录 517 新增，范围外 0；全新增工作字节与 Git 对象一致；原候选 1481 文件在提交中未改且工作字节一致。manifest.py --verify：516 项加清单自身通过。run01 的 16 项 Git pin（含原 B 反例、旧 0ab、独立 a7 对照）逐字节核实。既有输出目录试验在 mkdir 即拒绝，先于无效编译器启动，见 existing-output.txt。

run01 保存 120/3909，run02 最终 122/3949；原 33 回归明确复用，没有重复累计。原 B 记录器反向退出判据按实际 take/failed/acquire 核查，源码及 run_host 原字节绑定未换引用。Sanitizer 缺库明确 NOT_RUN；ARM/BSP、并发、RTL/CDC、实板及实时均未获批准。

规范观察：修改集中于两阶段批处理与有限代次选择，未发现需阻断的命名/重复/抽象问题。主机 C 同步只读 hooks 前提仍在；不要求此限定候选补生产异步证明。官方回归由主复核执行，本轴未重复运行。

审计方法记录：首次逐 git show 审计过慢中断，改 archive 批读；一次脚本遍历嵌套不同格式 bindings 遇 KeyError，收窄至本轮 run01 bindings 后完整通过，不将其计为产品失败。
