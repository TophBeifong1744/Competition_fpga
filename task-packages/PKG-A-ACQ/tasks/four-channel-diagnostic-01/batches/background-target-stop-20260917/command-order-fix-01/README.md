# S1 用户首次构建：辅助命令顺序误报修复

2026-09-17。范围仅本批检查器、回归测试和诊断归档；未修改实际F盘工程、采集源码、CMake、平台或硬件，未替用户构建或下载。

## 原因与最小修复

用户15:00:11执行Build，源码编译/链接完成，15:00:13被post检查拒绝：
`Generated commands/linker subarguments or gate mismatch`。

准确差异：预期 Ninja 命令列表为「前置检查、参数显示、编译、链接」，实际为「参数显示、前置检查、编译、链接」。这两个辅助节点之间没有依赖先后；实际 build.ninja 第45/47行仍把前置检查放在对象编译前，第62行仍保留链接前的依赖。编译和链接两条命令逐token一致，并无新增链接参数。

修复check_commands：只允许列表最前两条**原样完整命令**对调；仍要求恰好四条命令、各出现一次、编译和链接内容/顺序不变。没有排序编译/链接参数，没有忽略-Wl子参数或关闭检查。新增check_build_graph确认检查依赖仍在编译/链接之前。

原test_18此前引用实际F盘旧E1；用户安装S1后，该路径已经不是旧版本，改用既有冻结E1快照，保留“旧版本必须拒绝”的断言。

## 本轮验证

- [29项检查输出](../evidence/gate_20260917_150339_acd97a1e/stderr.log)：原21项（旧版本夹具改为冻结副本）+8项增量。覆盖实际顺序交换、缺失/重复/额外辅助命令、辅助命令篡改、编译/链接对调、交换后链接参数注入，以及检查依赖删除/重复。
- [只读产物核对](inspection_20260917_150453_00102838/result.json)：用修复前检查器重现原拒绝；修复后接受该命令排列。核对真实用户生成的源码、对象、ELF、map、BSP/XSA/工具和编译链接命令。新检查器正确拒绝沿用旧检查器产生的pre记录，要求用户重新Clean/Build。
- [原失败快照](before-fix/SHA256.json)：原检查器/策略/测试、用户源码、对象、ELF、map、build.ninja、编译命令、加载配置，以及完整pre/post检查目录。由preserve_failure.py一次性保存，已有目录拒绝覆盖。
- 主机C模型与完整源代码语法检查引用上一轮证据，源码未变，本轮没有重跑或记作新增模型/ARM编译。

已核对的**15:00用户构建**：

| 项目 | 结果 |
| --- | --- |
| ELF SHA-256 | 4b6a15f65c278f53cd898602733c83921108dd092b64f186437e30b3bde94598 |
| 对象 SHA-256 | 3fd07ea3b80a955c660291e4a38fbee2ca022bb10088f725dedea487ba4bc150 |
| 真实计时除数 | 333333343，对象重定位/ELF实际调用及运算核对一致 |
| 留存完整分配 | [0x00112A80, 0x00A3A700)，含首尾各64字节保护 |
| 留存数据起点 / 容量 | 0x00112AC0 / 9600000字节；不是本次实际已录长度 |
| 程序含堆栈终点 | 0x00A400C0，小于RX起点0x01000000 |
| DMA RX合同 | [0x01000000,0x01100000)，包8000、两槽8064，未变 |
| 加载路径 | 只读核对当前Run指向本应用ELF和已知连续四麦bit/ps7_init；未下载、未运行 |

这些地址只绑定此次用户生成的ELF。用户下次构建后仍须核对；实际导出地址和长度以通过检查后的READY日志为准，不提前执行导出。

## 用户下一步

原应用CMake通过绝对路径引用任务目录中的check_scene.py，修复已在此处生效；**不需再复制C文件，不需修改Vitis配置或Vivado。**

在Vitis对 four_mic_endurance执行 **Clean → Build**，看到 `S1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD` 后发来完整构建结果。先不Run。
必须Clean，是为了重新形成同一检查器版本下的前置检查、实际编译与产物检查，不将本次只读诊断伪装成新受检构建。

## 命令、清单与限制

本轮实际运行：

```powershell
# 本目录，首次保留原失败（不可重复覆盖）
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\preserve_failure.py
# 上一级批次目录
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\run_gate_tests.py
# 本目录，只读核对，生成新的时间戳输出
& 'C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B .\inspect_user_build.py
```

inspect_user_build.py固定关联本次失败快照：用户之后重建时，旧产物核对会明确拒绝，不应用它代替新构建检查。完整真实命令和objdump输出见inspection目录logs。

本目录SHA256.json为本次修复后的批次清单（路径相对上一级批次目录）。上一级原SHA256.json保留为初版清单，当前可变检查器/说明以此修复清单为准；历史源码和失败快照不覆盖。

本轮是作者诊断/修复，尚无B独立批准；不是实板通过、M1/H3或新阶段门。不提交、不推送、不合入。
