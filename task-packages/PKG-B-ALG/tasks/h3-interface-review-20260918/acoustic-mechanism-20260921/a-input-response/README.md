# 接收A输入依据回复及B核对

2026-09-21。来源：用户在当前任务转述的A集中回复；本文件为B摘要及核对，不冒充A签名报告，不宣称A已复核B研究。前置B提交b0a626bf06d7c0d07a10a158eee198ec8ca567de。

## A回复摘要（保留批准边界）

A未找到独立逐麦声学映射/四路同源差异标定报告；已有照片标签、同号接线确认和DATA1..4到mic0..3数字映射。八段metadata仍声明独立声学映射未验证。

A未找到固定延迟、相位、增益实测校准参数，参考通道/符号/单位/适用范围未知。mic0坐标原点不是校准参考证明。已检查链无逐通道补偿；共同CIC、乘32以及PC试听共同增益12都不是校准。

历史RTL依据为共同61.44MHz域、同一20分频状态、四路两级同步、共同phase==9使能、CIC3/R64/M1同复位/同抽取计数初值、乘32饱和signed24、4096组预热和共同编号。历史仿真支持RTL模型节拍/复位/编号同步，不证明引脚零偏斜或麦克风群延迟一致；外部I/O时序未完整约束边界保留。此次未重跑仿真。

八段配置仍为four-channel-continuous-s1-6s-raw-20260917-v1、ss-data-draft-0.3、c-adapter-user-square40-mic0-origin-20260913-v1。主机bit/ELF绑定不是FPGA读回身份，不能拿历史仿真bit哈希代替八段加载版本。

无独立精密坐标/高度/朝向/角度误差测量；沿用约1.5m/同高/目测角度和5cm操作者估计，不反推精确角度真值。主机WAV哈希一致，不代替手机文件核验。Xiaomi15Pro、85%、同WAV、可见音效关闭有操作者确认；手机端哈希、传输方式、播放器、隐藏DSP和朝向仍未知。

## B实际核对

verify.py只读比较Git对象与本地文件，完整结果result.json：

- GEOMETRY.md与df4b756ba49a2d161c03869a0a4a28034dad15b0逐字节一致。
- four_mic_top.v、pdm_cic3.v、continuous-prototype-01/RESULTS.md与88805ee415f137998b59b7cb197f2eeb988d17b7逐字节一致；已阅读两份RTL，同步和共同缩放结构与A陈述一致。
- 由已绑定八份metadata定位对应version-binding.json；八份文件与94b5fe79d87e038e895878fb31030cded469bb33逐字节一致，均记录bit b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf、ELF 4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6。
- 主机WAV重算ce28c5576eea620d8f358c0799bf8029cdc41bdeae8dcf95a02967d3bace6838，与A给值相同；未访问手机或板端。

运行环境Python3.12.14/Windows，仓库根执行：

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/acoustic-mechanism-20260921/a-input-response/verify.py
```

首次git show长对象路径触发Filename too long，在首份version-binding读取处退出128，没有产生有效结果。保留旧脚本verify-before-longpath-fix.py及failure.txt；改用git cat-file blob直接读对象后全项成功，不修改Git全局配置、不规避哈希验证。result.json为修复后结果。

## 更新后的判断

A输入询问已获得明确答复，不再重复要求同一批资料，也不等待不存在的校准报告。当前数字同步有设计依据，声学映射和固定延迟仍未校准；两者不能互相替代，更不能把未知直接断言为硬件故障。

lag-boundary、图闭合残差、峰形、联合取峰及4488帧完整回放已经完成，不因A回复重复执行。它们表明固定峰下的部分闭合残差不能由静态通道偏移消除，联合候选虽增加几何有效帧仍未恢复锁定。因此不能将标记峰差当校准值，也不能拟合本批名义角度后宣布独立性能。

当前优先动作：将累计B机制研究材料送A作限定复核，复核入口沿用acquisition-breaks/TO-A.md，但其中“等待输入依据回复”已由本记录收口；请求复核负结果和复现完整性，不再要求A重复输入回答。新算法试验暂不启动。若之后设计固定延迟诊断，必须先明确可辨识前提及独立校准/验证安排，不能用宽松门限绕过当前声学缺口。本轮不新增录音、不改A/C原件、不授予校准、稳定锁定或完整H3通过。
