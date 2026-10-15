# PYNQ 板端运行元数据采集

`collect_runtime.py` 为 C 平台工作收集只读运行事实，交给 #18 的 B 软件接合使用。Python 3.8 及以上，仅标准库。它不是 PYNQ 驱动或板级验收工具，不需要 root，不 import `pynq` / `numpy`，不初始化 Overlay、分配硬件缓冲或打开设备，不调用 MMIO、命令执行、网络、复位及编程接口。

当前没有已确认的板端 Linux/PYNQ 环境时，保留 UNKNOWN；不要为了填写报告先换镜像或操作硬件。由获授权的现场人员完成镜像选择和启动后，在**板端、后续应用实际使用的 Python 环境**运行：

```sh
python3 tools/pynq_platform/collect_runtime.py --help
python3 tools/pynq_platform/collect_runtime.py --out pynq-runtime-01.json
```

如只复制脚本到板端，将命令中的脚本路径换为该实际路径。`--out` 的父目录须已经存在，输出名必须是新文件。脚本以排他创建方式拒绝覆盖；中断或写入失败可能留下不完整 JSON，保留该失败事实并用新文件名重跑。

输出为单一 JSON，包含 UTC 时间、OS/内核 release、machine、Python 版本/位宽、允许的 `/etc/os-release` 字段、两个固定设备树入口的 model/compatible、MemTotal/CmaTotal/CmaFree。设备树仅是运行配置字符串，不能证明真实核心板型号、DDR 型号、速度等级或已加载逻辑。

`importlib.metadata` 读取当前 Python 环境内的 PYNQ/NumPy 发行包 Name、Version、Requires-Python，不执行包代码。缺包、缺字段、缺文件清单、权限和解码失败会明确记录。源码从 PYNQ 发行包文件清单中按 basename 白名单选取：dma、buffer、allocator/allocate、xlnk/xrt、device/embedded_device/xrt_device、overlay、mmio；只接受 `.py/.c/.cpp/.h/.hpp`。保留相对文件名、分组、尺寸与完整 SHA-256；无对应源文件时写 `NO_MATCHING_SOURCE_LISTED`。allocator 组只定位可能相关源码，不代表已确认当前使用哪个 allocator。未记录安装目录、用户名、hostname、设备序列号或网络凭据。

本工具依赖受信、正常的本地 Python 安装及其包元数据。`importlib.metadata` 内部读取 METADATA/RECORD 不经过本工具的普通文件守卫，Python 3.13 的 `files()` 还可能检查条目是否存在；该守卫不是针对恶意元数据的隔离机制。请勿在来源不可信或包含远端包搜索路径的 Python 环境运行；本地挂载形式的网络文件系统也不能由本工具可靠识别。

有现成的准确文件时，可以逐一增加显式工件哈希。例如，只有现场已经核对下列文件路径确实存在时才使用：

```sh
python3 tools/pynq_platform/collect_runtime.py --out pynq-runtime-02.json \
  --artifact /boot/BOOT.BIN --artifact /boot/image.ub \
  --artifact ./soundsight.bit --artifact ./soundsight.hwh
```

每项只按参数序号记录文件尺寸/SHA-256及读取状态，不复制内容、保存绝对路径或递归扫描目录；请在交接记录中按相同序号注明工件逻辑名称。拒绝非普通文件；全部原始 UNC 工件路径在任何路径解析之前拒绝。应传本地稳定文件；脚本不能识别所有通过本地挂载呈现的网络文件系统。哈希只说明指定文件的内容，不能证明该文件已启动/加载，也**不能证明 bit 与 HWH 同构建匹配**。原始安装镜像 SHA-256 无法从已运行的 rootfs 反推，须另从原始下载/交付镜像取证。

固定文本每项最多 64 KiB；PYNQ 源码最多 64 文件、每文件 2 MiB、合计 16 MiB；工件最多 16 文件、每文件 2 GiB、合计 4 GiB。分块读取，并用最多额外 1 字节判断增长越界；超限/读中变化不输出摘要。包文件清单最多接受 20,000 条，字段最多 512 字符。`importlib.metadata` 自身解析发行包元数据/文件清单没有硬字节上限；这些边界是本工具对输出和后续文件读取的限制，不是文件系统 I/O 的时间上限。运行时的缺项/读取错误应查看 JSON，终端退出码不替代逐项核查。

| 退出码 / 状态 | 含义 |
|---|---|
| `0` / `ZYNQ_RUNTIME_METADATA_ONLY` | 已写报告；Linux、ARM machine 与设备树 Zynq compatible 字符串相符，仅为元数据观察 |
| `3` / `NON_BOARD_ENVIRONMENT` | 已写报告；不满足上述运行环境字符串条件。Windows 必定走此路径；缺设备树也不能冒称板端成立 |
| `2` | 参数/输出/未完成报告错误；已有输出拒绝覆盖 |

所有硬件字段始终为 `NOT_RUN`，没有 PASS 输出：物理板身份、镜像启动来源、Overlay、bit/HWH 匹配、MMIO、IRQ、DMA、allocator、cache/barrier、缓冲退休及停止/超时恢复。即使退出 `0`，缺包或源文件读取失败仍可能存在；版本/源码哈希不能替代缓存一致性或退休验证。

下一步将原 JSON 与本次 Python 环境、人工启动记录、原镜像身份及工件参数序号对应关系一并交 #18。先核缺项，再由 A/C 当前硬件合同与 B 软件合同确定后续验证入口。该采集器没有地址/偏移、寄存器 ABI、IRQ 清除、DMA 所有权或屏障操作，不需要 ILA；现有接口未绑定项继续保留 UNBOUND。本次命令不改变原 Vivado/Vitis 工程，也不授权启动或操作板卡。
