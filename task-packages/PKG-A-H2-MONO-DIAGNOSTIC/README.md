# A → B：首批单麦诊断录音

2026-09-10；负责人 A，交 B 复核；状态：单麦 diagnostic 导出整理，**完整四路 H2 仍缺**。没有推送或合入，也没有新增录音、加载或工程改动。

## 可直接使用的材料

- `data/quiet_03/`、`data/music_04/`：各有 `samples.csv` 与 `metadata.json`，每份 48000 行样本；配置 48 kHz，名义 1 秒，真实采样率未测。
- `originals/mono_acceptance_20260910/`：原样复制工程交付，含两份 BIN、原幅度 24bit WAV、串口转录、源码与采集后工程快照及原清单。原文件名不改。
- `evidence/`：A 原复核、有限收尾决定、问题单，以及本包导出验证记录。旧文件保留当时状态，不覆盖历史；以有限收尾决定和本说明明确当前边界。
- `source/mono_delivery.py`：移植已有解码规则并补充来源、配置/加载区别、哈希及字段检查，不重新实现采集。`decode_mono_original_reference.py` 仅供追溯，**不要用它交付**，因其无条件标记 hardware-audio。

来源是用户标注的安静/歌曲采集，并有对应用户粘贴串口记录；不是本聊天独立现场观察。A 最新转达用户试听歌曲较清楚，无明显嗡声、断续、失真。该主观反馈不证明电气、IO 时序或最终音质。

## B 的读取与验证

Python 3.10+ 标准库即可，无 NumPy 依赖。从本包根目录执行：

```powershell
python -B source/file_manifest.py verify
python -B source/mono_delivery.py verify
python -B source/test_delivery.py
```

复现导出（目录必须不存在；建议保持在本包根目录下，以保留元数据相对路径）：

```powershell
python -B source/mono_delivery.py export --directory reproduced
python -B source/mono_delivery.py verify --directory reproduced
```

读取 CSV 用 Python `csv.DictReader`，将 `sample_id`、`pcm`、`flags` 转成整数。ID 是原始 uint64；不得先转 float、重编号或拼接两次捕获。若用 NumPy，ID 应使用 uint64。脚本复核逐字节 CSV 与原 BIN 对应关系、元数据内容、FNV、连续区间、符号范围、标志、串口统计及 WAV 逐样本一致性。

## 独立合同：ss-mono-diagnostic-0.2

这不是 `ss-data-draft-0.3`，不要直接送入四路 H1 读取器或六麦定位入口。0.2 是本包本地单麦合同版本，等待 B 复核，不表示替换公共 H1。

CSV 列固定为 `sample_id,pcm,flags`，仅一个逻辑输入 mic0；物理模块序列号未知。BIN 为小端，每条 16 字节：ID low32、ID high32、PCM signed32、flags32。保留原始值；未做去直流、滤波、增益或补样。flag bit0 为保留溢出，bit1 为输出饱和；未知/错误位拒绝干净导出，原 BIN 始终保留。

PCM 是 signed24 码值、以 int32 承载。PDM 0→−1、1→+1；CIC3 R64 M1 增益 262144，结果乘 32 再 signed24 饱和。两份实录均为 32 的整数倍；24 位容器不是 24 位有效精度。`pcm / 8388608` 仅为相对满量程归一化，不是声压。

| 录音 | 原始 ID 区间 | FNV-1a32 | 样本数 |
|---|---|---|---|
| 安静 quiet_03 | 14223–62222 | EFFF882A | 48000 |
| 歌曲 music_04 | 13352–61351 | C7762DD9 | 48000 |

两段编号各自连续、flags 全零，但不是一个共同连续时间轴；两次之间复位/触发的精确时刻未知。连续编号和零标志不排除所有未观测采样错误。

## 来源与未完成项

元数据使用 `source_kind=user-reported-hardware-audio`，避免把解析成功当作物理来源证明。串口是用户粘贴转录，不冒称串口工具原始日志。

每段包含原 BIN / CSV / 串口转录 SHA-256 和采集后源码、bit、ELF、XSA 快照哈希。配置标识为 mono-capture-v1，转录打印 build Sep 10 2026 14:48:35；**实际加载身份未强绑定**。采集后快照及文件相互一致不能倒推当时加载字节。本包也未绑定 Git 提交。

麦克风坐标、声源方向/距离、实测采样率、有效精度均以 null/未知记录。配置 PDM 3.072 MHz、PL 61.44 MHz 不当作测量值。仍缺 VCCO/VDD、外部 CLOCK/DATA 时序、准确加载关联；低频占比高与启动偏置衰减原因未明。保留问题，不用高通或增益掩盖。

本包仅供 B 做单麦格式、数值与真实输入初步诊断；不是精度、SNR、音频增强或完整板级验收。完整四路同步采集与四路 H2 未完成；本轮不扩通道、不安排测量或重录。B 可继续其软件预算和 H3 材料。
