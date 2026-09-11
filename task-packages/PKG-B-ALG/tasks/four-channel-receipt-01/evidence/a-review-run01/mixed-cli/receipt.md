# 四路输入诊断回执

状态：PARTIAL_OR_REJECTED；可解析 1，拒绝 1。

仅文件与数值诊断；来源、物理映射、同步、采样率和声学效果未独立验收。

## multiple-errors

输入：`E:\ss-four-channel-review-01\task-packages\PKG-B-ALG\tasks\four-channel-receipt-01\evidence\a-review-run01\cases\multiple-errors`

拒绝：integer_range: mic0 at CSV physical line 2: expected -8388608..8388607

修订导出器或元数据并交新版本；原始文件保持不变。

## restart

输入：`E:\ss-four-channel-review-01\task-packages\PKG-B-ALG\reference\h1-ss-data-draft-0.3\payload\examples\h1\restart`

4路，2样本；ID 0–1。
配置 `h1-code-config-0.1`；来源 `synthetic-code`；错误行 0。

| 通道 | 最小/最大码 | 均值 | RMS | 满量程端点数 |
|---|---:|---:|---:|---:|
| mic0 | -101/101 | 0.0000 | 101.0000 | 0 |
| mic1 | -201/201 | 0.0000 | 201.0000 | 0 |
| mic2 | -301/301 | 0.0000 | 301.0000 | 0 |
| mic3 | -401/401 | 0.0000 | 401.0000 | 0 |

观察：GEOMETRY_OR_CALIBRATION_UNVERIFIED, INSUFFICIENT_CLEAN_PAIR_SAMPLES, NOT_REAL_AUDIO_RECEIPT

先核查错误/可疑通道及来源；可解析不等于采集验收通过。

错误原行及位置见 errors.json；完整连续区间、每路统计、相关性及输入SHA见 summary.json。
频繁相似度提示需要结合声源/码型解释，不能证明复制、同步或物理映射。
