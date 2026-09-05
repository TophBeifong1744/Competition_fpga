# 系统架构

## 1. 目标边界

SoundSight 的最小闭环是：四路同步采集 → 已知方向声音输入 → PL 输出稳定 TDOA/DOA → 波束自动指向 → 增强音频输出。MVP 不包含语音识别、声纹识别、复杂多声源分离或由 PS/Linux 代替核心定位计算。

## 2. 数据面与控制面

### PL 数据面

```text
4ch mic interface
  -> channel align / sample valid
  -> DC blocker / decimation / FIR
  -> frame + window + overlap buffer
  -> FFT scheduler
  -> cross spectrum + PHAT weighting
  -> IFFT + legal-lag peak search
  -> sub-sample TDOA
  -> geometry solver + confidence
  -> steering-delay generator
  -> per-channel delay line / fractional delay
  -> sum / gain / saturate
  -> audio output and debug stream
```

设计要求：

- 四通道样本必须携带同一 `sample_valid` 语义，通道顺序固定且可追踪。
- 流接口优先使用 AXI4-Stream 语义；配置与状态使用 AXI4-Lite。
- 每次跨时钟域都必须显式使用异步 FIFO、握手同步器或等价结构，不能依赖仿真恰好通过。
- 每级记录数据宽度、二进制小数位、最大增益、舍入和饱和策略。
- 所有 FIFO 溢出/欠载、帧丢失和非法 TDOA 都应有黏滞状态位与计数器。

### PS 控制面

PS 负责：

- 写入采样模式、帧长、阈值、阵列坐标、声速、滤波器系数和手动/自动波束模式。
- 读取 DOA、置信度、帧号、错误计数、峰值质量和性能计数器。
- 驱动 LCD/UART/网络 UI，记录小规模调试数据并管理实验元数据。
- 在开发阶段触发原始帧抓取，但不进入实时音频关键路径。

## 3. 时钟与复位

M0 必须画出真实板级时钟树后才能冻结本节。最低要求如下：

- 所有麦克风通道共享同一采样时基；禁止用四个自由运行的采样时钟拼成“同步”阵列。
- 采集时钟域与 PL 处理时钟域的转换有明确缓冲、满/空策略和复位顺序。
- 复位释放同步到各自时钟域；复位后帧号、延迟线、FFT 状态和统计计数的行为可预测。
- 音频输出与输入若使用不同采样时基，必须定义异步速率匹配方案。

## 4. 帧与延迟预算

初始算法基线为 48 kHz、1024 点帧、512 点 hop：一帧约 21.3 ms，方向更新间隔约 10.7 ms。系统目标“定位刷新不高于 50 ms”还包含缓存、FFT/IFFT、求解和 UI 传递时间。

最终参数需用以下约束共同决定：

- 阵列最大物理时延与合法 lag 搜索范围；
- 低频定位所需频率分辨率；
- BRAM/DSP 资源与 FFT IP 吞吐；
- 方向刷新率和波束切换稳定性；
- 房间混响下的峰值可靠性。

## 5. 模块接口冻结顺序

1. `mic_rx`：硬件接口、通道顺序、采样格式、`sample_valid`。
2. `audio_preprocess`：输入/输出采样率、定点格式与群时延。
3. `frame_buffer`：帧长、hop、窗函数与 backpressure。
4. `gcc_phat_pair`：通道对调度、FFT 格式、归一化近似和 lag 输出。
5. `tdoa_doa`：坐标/声速格式、异常拒绝、角度和置信度格式。
6. `delay_sum`：最大延时、更新边界、插值结构、增益和饱和。
7. AXI 寄存器表：地址、复位值、读写权限和原子更新机制。

接口变更必须先更新本文件或对应模块说明，再更新实现与测试。

## 6. 需要尽早验证的风险

- 麦克风模块是否能共享时钟并保持固定通道延迟。
- Zynq-7020 板卡 IO 电压、可用引脚和音频输出链路是否匹配。
- 麦克风间距是否在空间混叠、阵列尺寸和目标频段之间取得合理折中。
- PHAT 归一化的定点近似是否在低能量频点放大噪声。
- 单 FFT/IFFT 复用能否在 hop 周期内处理全部通道对。
- 混响、多径和双声源是否导致峰值跳变；置信度与平滑不能被省略。

