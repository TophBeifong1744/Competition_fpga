# B限定复核：A 9/18工程合同与预算收口

审核SHA：f08556d01821d6c3c8204fdac2c38f53b2107c05；分支codex/toph/h3-production-readiness-20260921。基线cf026cf29518488f8c7275b825f3487a8d892f80，dce7b81首次交付及f08556d发布状态补记；共29新增文件。实际2026-09-21，独立短路径F:/NUEC/r/ready，作者原件未改。

结论：**限定PASS**。仅批准A侧候选合同决定稿、逐级golden缺项计划、16服务条件预算计算器与证据归档；不冻结生产ABI、数制profile或硬件映射，不批准ARM/BSP、AMD/RTL/CDC、实板、实时或完整H3。

## 集中裁决

1. **路线候选可继续**：PS accepted-row/帧/所有权/提交与后续独立PL数值服务分工合理。C独立滑动窗＋2输出帧的178856B是主机布局，不沿用旧202816B或相加；ca512a8已获独立限定批准，原“待审”由发布头正确覆盖，本轮不重审。
2. **DAS/ROM决定范围**：接受8前视/17历史、2beam＋最新pending、PS DDR只读ROM552960B作为下一实现候选，旧9前视profile不改。480淡变与最长960样点平滑回mono仅适用于audio_smooth_stop；fatal/session_abort必须撤销逻辑结果/未消费输出并交运输层停止排空，不能被淡变掩盖。这里确认需求分离，不确认硬停设备实现。DDR地址/cache/带宽及实际两bank生命周期仍未验证。
3. **生产边界**：内部session/generation uint64、有限计数、不可变96B身份、commit/take TTL及全状态闭合沿用准确软件合同；boot/UUID映射、规范化hash生成、required_status生产集合、可信时钟锚、ISR队列/屏障仍待定。all_required_status_visible_at≤available≤commit_now及source/emit偏移必须绑定同profile，不能借此批准d3d旧检查器。
4. **数制/golden**：fixed4、S23/S28及归一化CORDIC均候选，输入域/中间位宽/误差证明分开。portable Q30和AMD24不共用逐码期待；新S25 gate域不能无条件继承原S24/FFT196帧覆盖。表中已完成软件/FFT/PS检查按准确版本复用，仅列实现差异与新增域，未重复派旧FFT/录音/耐久。
5. **预算**：hop=4/375秒，100MHz整数限额1066666；不同频率先以有理秒相加，历史8×7366+6×7406=103364不当总WCET。H1输入1536000B/s；平均hop16384B与完整250行包相位最坏24000B分开。有限队列条件initial+burst+ceil(r*T)且R≥r与所述到达/服务包络相符；实际burst/T/R未测，不能从空环8包容量推出容许停顿。16服务上界和系统总内存仍null，总状态REALTIME_BLOCKED。

## 实际运行 / 复用 / 未测

Python3.12.14，标准库。先读PUBLICATION再READINESS、CONTRACT、GOLDEN-GAPS和JSON/源码。

仓库根执行 `python -B task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/check_readiness_20260921.py --out F:/NUEC/review-evidence/readiness-f08556d/run01`：退出0，30项/11准确来源通过；实际argv、环境、来源blob/SHA和完整结果见run01。仅进程safe.directory，不改全局Git配置。

B independent.py另检查全部250包相位、16混合频率/逐项未知服务、252组队列边界及3类未知queue参数，均通过。Spec轴probe.py另11个边界包含截止等号/一周期超限、纳秒临界、持续率不足，均通过；详见spec/。这些是数学与拒绝行为检查，不是实测服务保证。

完整性：29仅新增、原文件修改删除0，准确Git字节匹配；三OUTPUT清单18项、11准确Git源、run02/clean02各5源hash及4链接通过。已有输出目录在运行前拒绝。作者Git所有权128失败保留；run01/run02不合计60项。

复用原明确批准的PS桥/动态DAS/节点/FFT等子项，本轮不运行其技术测试；既有主机sizeof不推导ARM。未运行AMD/IP/RTL、ARM、综合实现、CDC、真实DDR/cache、板测、声学性能、采录或耐久。

## Standards

无硬阻断。准确来源和失败历史保留；清单按原字节复核，不格式化历史CRLF。非阻断观察：queue字段未全给出时，已给出的非法负数等可能未独立验证，结果仍None/REALTIME_BLOCKED，故本检查器是固定合同条件计算器，不是通用生产schema验证器。未来开放配置输入前应完善逐字段诊断，不能把本PASS当输入schema全覆盖。

## Spec

无本申请范围内阻断。候选决定与已冻结/待定/未验证字段分列；未找到合同内false条件通过。全状态可见时间、纯整数身份、采样时基与各golden来源不混淆。

## 与其他复核隔离

本包固定引用d3d2a3d，不替换其原证据，也不由本轮关闭R1/R2。复核期间本机取得新main e4ac088，其A报告已独立关闭准确ad30bda的R1/R2；仅注明外部后续状态，原d3d失败仍为历史，不能将那项批准归功于本合同包。ca512已批准同理。

网络fetch/ls-remote遇重置/超时单列为发布环境问题，不影响固定对象实际检查，但在完成远端核对/推送之前不声称本次发布完成。允许本29文件和B包外复核记录归档入库，研究入口保持任务包，不改默认算法或真实one/Vitis。规范轴0阻断、需求轴0阻断。
