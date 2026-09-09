# 首批硬件测试码型交接

本目录数据来自用户提供的本次实板串口输出。日志中的 Markdown 下划线转义已还原，换行规范为 LF；不是串口原始字节文件。samples.csv 逐行提取 BEGIN_SAMPLES_CSV 与 END_SAMPLES_CSV 之间内容，没有用 golden 生成数据。

- 实收两包，每包24字节，共4组四通道值，编号0..3。
- 程序报告DMA、长度、逐字比对和保护区检查通过；错误0。
- 硬件测试码型 / diagnostic；不是麦克风录音，不证明声学H2或一小时长稳。
- 48000仅为格式接口的名义占位值，不是测试源实测采样率；禁止由它推算时长/声学方向。坐标未知。
- B读取器由当前工作区复制并保存哈希。验证结果见 validation.json；通过仅表示当前读取器实际解析及码型对照通过，人工接收仍由B确认。
- software与hardware保存当前磁盘快照，不能单凭快照证明本次板上实际加载的文件身份。reported build只是日志中的编译时间，不是采集时刻。

## 复核

使用含numpy的Python运行：python -B validate_capture.py

脚本加载本目录reader/h1_reader.py，检查CSV与日志原始字/独立golden一致、原始编号、无错误、无BOM及证据边界，输出validation.json。不修改CSV或metadata。文件身份见manifest.json。

