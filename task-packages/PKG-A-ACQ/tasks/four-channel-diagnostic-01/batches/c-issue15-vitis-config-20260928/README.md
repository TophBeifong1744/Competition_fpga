# #15 两批录音的 Vitis Run 配置补证

2026-09-28，C/hsc119 提供三张 Vitis Unified IDE 2025.2 截图，并事后确认：室内 `sound_09_22` 与户外 `sound_otd` 两批录音当时实际使用同一个 `vitis-capture-import_app_hw_1` Run；截图所示 ELF 和 bit 文件自录音以来未替换或改动。此项为操作人回忆确认，不是采集当时自动留存的运行日志。

本目录原样保存三张截图和当前本机 Vitis 工作区的 `_ide/launch.json`。截图显示 Baremetal Debug、Local、Auto Detect、TCL 初始化、运行 `ps7_init` 与 post-init、整系统复位、Program Device、`ps7_cortexa9_0` 加载 `four_mic_endurance.elf`。配置文件给出可检验的完整路径；其中 `resetSystem=true`、`programDevice=true`、`runPs7Init=true`、`runPs7PostInit=true`、`resetAPU=false`、`resetProcessor=false`、`skipRevisionCheck=false`。这些是配置值，不是本次重新执行下载或板上回读的证据。

| 保存文件 | 来源 | SHA-256 |
| --- | --- | --- |
| `vitis-launch-top.png` | 用户第 1 张截图 | `6e453af263df93c954916bb51bbb4dd7e94de4584332111236ce4eca07971905` |
| `vitis-launch-processor.png` | 用户第 2 张截图 | `984b6cc105d8c2c6e1e876c00ef426fca1aac87114ee58ff5ad701a85d37fdbb` |
| `vitis-launch-elf-summary.png` | 用户第 3 张截图 | `7b5ad772416a2fa0437b908507d59d16a3fae1a6b6d947b5ab45a2f6a9d6a3ec` |
| `launch.json` | 当前工作区 `_ide/launch.json`，原字节复制 | `060366a4faab009515a3c6faf20c170ed739183b5efd8f98e0a38175c6417590` |

当前本机工作区为 `C:/Users/hsc/Documents/Codex/2026-09-20/wo-m/outputs/vitis-capture-import`。只读核对其文件；并未修改或执行实际 Vitis 工程：

| 工作区相对路径 | 字节数 | 本次 SHA-256 | 文件修改时间（本机时间，仅作线索） |
| --- | ---: | --- | --- |
| `files/four_mic_endurance.elf` | 308168 | `4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6` | 2026-09-22 10:52:25 |
| `_ide/system_continuous_20260915/system_continuous_20260915.bit` | 4045690 | `b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf` | 2026-09-22 15:38:16 |
| `_ide/system_continuous_20260915/ps7_init.tcl` | 27896 | `a158fcc7d723b21003864159006e781ffaf5e8df24ec9b1d9279f9d14ff3ee5e` | 2026-09-22 15:38:16 |
| `files/system_continuous_20260915.xsa` | 612051 | `b84e93631132a3838cc9dadc1ce9037f2685d4d10de0b1655c76291663a8f60b` | 2026-09-17 17:26:43 |

ELF 和 bit 当前哈希与先前候选记录相同。结合 C 的“文件未变”确认，可将两批的 Run 配置和主机文件身份标为**操作人事后确认，并由当前文件哈希佐证**。尚无采集当时自动保存的 Run 控制台、加载前检查或板上读回；A 仍应核对这是否为当时获批的加载入口。此补证不解决录音尾部完整性、摆位测量和试听缺口，也不构成 #15 或后续阶段 PASS。
