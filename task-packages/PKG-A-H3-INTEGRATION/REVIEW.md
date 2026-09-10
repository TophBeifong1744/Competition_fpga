# A 自检与 B 待复核记录

状态：**A 工程约束整理完成，待 B 复核；未自行合入，不代表H3通过。**

- 基线 main：9878ccafdda6cd5a522cc9de95c1277bcee70f08；实际fetch与ls-remote相等。
- 新分支：codex/toph/h3-fpga-integration-constraints。
- FFT候选来源：ac0ff38e954dac094fd84e28b329dcb24dded7fb；独立实验、待B复核，非本main已获准模块。
- 本包版本：a-h3-integration-constraints-0.1。最终提交号通过Git记录定位，避免把本包提交自身SHA写入后再改动。

## 已执行与证据

1. 主线资料与FFT材料按确切Git blob归档，本机单麦源码/BD/实现报告按显式路径归档，47份来源记录带SHA-256。未修改来源。
2. source/calculate_budget.py复算帧/hop、四/六通道接口算术、两个时钟场景、CIC理想群延迟、FIFO/DDR界限，并从原cycles.csv重算7402/7406/7641。
3. 11项测试通过；首次日志 evidence/tests.txt保留文件句柄ResourceWarning。随后改为with关闭读取句柄并通过完整复跑，见 evidence/recheck/tests.txt；未删失败或初始记录。
4. FFT作者归档验证入口重新生成参考并核查原22528个复数输出、22次变换；21份原哈希、输入码一致，浮点参考最大差0，原输出/周期检查通过。**不是本次新XSim、综合、P&R或板测，也不是独立位精确C模型。**
5. 完整便携入口 source/verify.py，结果见 evidence/recheck/result.json；预算数值/语义一致，字节不一致。首次Windows文本输出为CRLF，复跑write_bytes为LF；归一化换行后字节一致，保留两份原件，不把换行差异误判数值退步。

## 初始环境与采集修正记录

- 沙箱fetch不能写FETCH_HEAD，提升权限后只读远端并正常fetch；未推送远端main。
- 首次新工作区检出因Windows路径过长失败，Git自动清理失败工作区；以单次core.longpaths=true重试完成。未改全局Git配置、未覆盖用户文件。
- 首次来源提取使用大写REVIEW.md，Git实际路径为review.md；随后固定大小写并使用cat-file blob规避路径探测问题。恢复时已有文件逐字节相同才复用，没有替换不同原件。
- 全包git diff --check会报告原始CRLF及供应商报告行尾空格；本包用 -text 保留证据字节，不能为了格式检查清洗快照。作者新增README/REVIEW、payload、source和.gitattributes单独执行空白检查；references/evidence按哈希与数值核验，不宣称原始报告全无空白告警。

## B 需重点复核

100MHz独立FFT候选与61.44MHz单麦域不能混作同域；8000周期服务槽/20%余量是规划；64ms首次捕获与50ms刷新是不同指标；完整音频端到端上限和整机资源仍U；PHAT epsilon缩放、IP溢出拒绝、几何秩与因果DAS均须后续golden。H1是文件合同，不是多路DMA已冻结。

允许范围仅为本任务包的约束、算术脚本与依据归档；不批准默认算法变更、六路采集、四麦声学模拟、采购或新RTL，不批准实板H2/H3。B复核时补充实际审核提交SHA、命令、问题、通过/需修改与允许范围；A不代签B。
