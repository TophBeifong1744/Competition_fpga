# 运行元数据采集工具复核

2026-10-15；仅针对 `tools/pynq_platform/collect_runtime.py` 和同目录 README。没有验证 PYNQ 板卡、驱动、镜像启动或 Overlay。

作者为 C 指定 AI 的独立实现代理；复核为未继承作者上下文的 `independent_reviewer` 代理。结论 **PASS_WITH_LIMITATIONS**，不是 GitHub 原生 Approve。

## 独立预期

显式新 JSON 排他创建，不覆盖已有文件；仅取固定运行元数据、标准库包元数据、限定源码和显式普通工件哈希。不得 import PYNQ/NumPy、执行子命令、调用网络/寄存器/设备/DMA/复位/编程；Windows不冒称板端。运行元数据和哈希不能证明物理身份、镜像启动来源、bit/HWH同构建、缓存或缓冲退休。

## 发现和修复

首轮发现 MEDIUM：原 `--artifact` 在 UNC 路径拒绝前调用 `Path.resolve()`，Windows可能先访问远端共享。作者已改为所有原始 UNC 工件在任何路径解析前统一拒绝。

LOW 范围问题：`importlib.metadata` 内部读 METADATA/RECORD 不经过普通文件守卫，Python3.13的 `files()`可能先检查条目存在。README已明确受信、正常、本地 Python 安装前提；不宣称隔离恶意发行元数据或可靠识别本地形式的网络挂载。

## 准确候选与证据

```text
collect_runtime.py  65c642c94bdae2d79a590974592469484919277a879c2812341495d0f67f7201
README.md           1dd91f1d8d31c96b96bc757356efbadf48088c8cd0440304566c85224696593a
```

作者在本机 Python3.13.5 完成语法/compile/--help、Windows报告、硬件NOT_RUN、未import PYNQ/NumPy及覆盖拒绝检查；AST按Python3.8语法解析，不声称实际Python3.8运行。初次系统临时目录写入受沙箱拒绝，改用工作区诊断输出后成功，未改变权限。

独立增量复核在内存中跑9个mock用例，覆盖反斜杠/正斜杠/扩展UNC、第二工件为UNC、UNC输出及直接读入口；每例 `Path.resolve/exists/open`、`os.open` 和 `builtins.open` 调用数均为0。内存中移除新增守卫的负例被捕获，证明检查能检出原问题。未访问网络或设备，未运行采集器来查询板卡。

没有剩余 BLOCKER/HIGH/MEDIUM。真实 Python3.8、板端Linux/PYNQ及全部硬件验证仍 NOT_RUN/UNVERIFIED。包元数据解析与文件I/O无硬时间上限；运行报告须逐项读缺项/错误，不能只看退出码。
