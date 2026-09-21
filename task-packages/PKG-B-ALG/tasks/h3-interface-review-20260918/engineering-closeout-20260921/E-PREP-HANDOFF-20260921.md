# E准备交付依赖与B合同对照（2026-09-21）

已采用2026-09-17增量复核。本文件是B侧对照及供用户转交E/W的交接材料，**不是E完整准备子包，也不是跨任务送达回执**。不新建任务包，不改A/E原件或主流程状态，不操作实际工程。

## 准确范围与来源

- 本次新增仅本文件和同目录 `e-prep-source-check-20260921.json`；无算法、合同参数、生成器或向量变更。记录在原B工程任务分支，作者整理待独立核对，不自合main。
- 派工来源：main `704407e19f25a5405ef4d8f0272e977224e69b2c` 的 `docs/phases/2026-09-13-to-10-01/dispatch.md`。该记录同时写明E报告已有准备、文件尚未提交，不能当实际交付清单。
- A来源：`f08556d01821d6c3c8204fdac2c38f53b2107c05` 下 `task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/PRODUCTION-CONTRACT-20260921.md`、`GOLDEN-GAPS-20260921.md`、`service-budget-20260921.json`。限定批准见主线 `docs/reviews/readiness-f08556d/B-REVIEW.md`。这些是已发布旧准备依据，不是E这次未提交成果。
- B来源：本地对象 `3c04a8c221a3808846e749c8814ad22a85e8e13d` 的 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/delay-consistency-01/DISPATCH-20260921-B.md`。读取了准确原文；未核实其直接远端发布，不声称E已取得该版本。
- A原合同中ca512待审、d3d待修等历史状态按已发布ca512a8及ad30bda独立批准解释，不修改冻结原文，不重跑已关闭项。B来源的“仅一段录音”段落已被上述main派工顶部的新八段安排覆盖，本交付只引用其合同表，不派录音任务。

## 已核实合同意见

“一致”仅指上述两个准确文档的候选方向一致，不表示E当前未交付表已确认，更不构成双方生产冻结。每行实际工程证据均未由本次取得。

|项目|一致部分|待决与实际工程证据|责任|
|---|---|---|---|
|H1/分帧/身份|沿用1024/512及不可变config/geometry/numeric身份|规范化hash、boot/session映射、DMA所有权及缓存屏障绑定|E落实，B核对，A裁决|
|FFT/fixed4|固定RNE右移4、FFT29→S25独立候选；reference25保留|profile/hash、缩放及弱信号边界；activity去均值S25新增域不得借用S24旧向量通过|E交145向量原件及准备日志，B审影响域|
|PHAT/IFFT|epsilon按互谱幅度码；portable Q30和AMD24分别列golden|实际核、版本/配置、mask/阈值码绑定；后级AMD逐码差异未测|E准备及工程绑定，B判合同|
|DOA/CORDIC|S23及归一化S28为有限域候选；旧格式保留|除法/舍入临时位、小向量精度及实际核，容纳范围不等于数值正确|E实现证据，B核对数值|
|动态DAS|8前视/17历史、2beam+最新pending、480淡变；旧9前视另列|bank/cache/有界背压；覆盖pending不保证逐请求执行；实际输出舍入/饱和及profile绑定仍需证据|E工程，B语义|
|STOP/reset|平滑STOP最长960样点（48kHz约20ms）回mono；fatal/session_abort硬撤销|运输停止/drain及未消费输出撤销；不能用平滑淡变解释硬停|E运输层，A接口裁决|
|source/emit/TTL|source=emit−8；仅真EOF补尾，gap/reset不补零；严格整数；停顿不暂停TTL|真实时钟锚、ready/expiry时基显式转换；HOLD不续期、flush与背压的实际绑定|E时基/工程，B核对|
|完成/提交|all_required_status_visible_at≤available≤commit_now；commit/take查身份及TTL|按实际16服务枚举required_status全集，不冻结夹具status=3；late error、session/config/status及真实异步提交证据|E列全集，B核对，A裁决|
|ROM/内存|552960B只读DDR驻留为候选，未批准默认部署PL|ARM布局/地址/cache/带宽/同时存活峰值；178856B主机布局与107496B、202816B旧模型不可相加；103364周期槽不是WCET|E实测/布局，B预算检查|

## E原件缺项与W发布边界

本会话已检索可访问 `F:/NUEC` 工作区的普通/忽略文件及已发布Git目录，未找到下列新成果。用户随后确认也尚未取得目录或SHA。**结论为未取得，不推断E未生成或丢失。** 当前机器、已发布树的观察不能代替E本机核查。

|必须交付的原件|当前状态|E一次回报内容|
|---|---|---|
|E-CONTINUE-20260921.md及profile确认表|路径/内容未取得|实际绝对路径、来源及当前版本|
|16项服务测量方案|原件未取得；旧预算JSON可读，但不是新测量表|表路径、每项实现/构建/配置与测点、频率/单位、启动/II/争用/暂停条件及上界依据|
|145个fixed4待测向量|输入及逐项清单未取得，数量仅为派工记载|向量路径、清单/哈希、生成脚本及配置、准确命令与依赖|
|准备结果、原始日志、失败记录|未取得|实际执行命令、退出码、结果与失败；区分生成/格式检查和数值/硬件验证|
|E工作区Git身份|未知|原工作区绝对路径、分支、HEAD，以及上述文件逐项已提交/未提交状态|

E若找到原件，保留唯一写入位置，按以上范围交W；W核对清单后发布准备专用范围并返回直接远端准确SHA及统一入口，不等待16服务全部实测。若E本机也找不到，E逐项确认“未生成/未保存/无法定位”，由W/主流程纠正进度登记；本任务不代改公共状态。

已发布预算的16服务ID为：capture_dma_cache_copy、accepted_row_frame、mean_two_windows、fft8、fixed4、gate_power_state、cross_mask_phat、conjugate_ifft6、lag、doa_cordic_tracker、rom_control、das_two_beams、config_status_commit、arbitration_cdc_reset、output_backpressure、audit_drain。已发布模型的cycles_per_hop均为null；旧8FFT+6IFFT槽103364周期仅为历史参考，不能填入16项真实上界或推定实时。输出8槽不能替代burst/blackout/最低服务率证明。E尚未交回的测量不填写为零或PASS。

## 本次实际运行、复用与未测

- 实际：安全fetch、读取准确Git对象、检索可访问文件、逐行文档对照。`e-prep-source-check-20260921.json`保存来源Git对象/退出码/路径及文档身份一致性检查；这是来源检查，不是工程或数值测试。
- 复用：f08556d合同/预算限定批准、ca512a8桥接及ad30bda工程返修批准，动态268e526旧证据；不重跑已批准数值、33/122/30项或旧返修。
- 未测：E的145向量生成及准备检查（原件缺失）、新fixed4 AMD/RTL验证、16实际服务上界、真实ARM内存布局、DMA/DDR/仲裁/CDC及有界背压；未运行Vivado/Vitis、未修改one工程或建立副本。无本次数值失败记录可交付；原件缺失不记作数值测试失败。
- 结论：准备子包交接处于WAIT_E_SOURCE_DELIVERY；完整H3仍未通过，REALTIME_BLOCKED。不能以文档对照或输入生成代替生产实现、AMD、RTL或实时通过。

## 接续与集中复核提示

E负责定位原件及回报，当前无法给出有依据的到件时间；W在原件齐备后即可发布准备范围，无须等待硬件。B收到准确已发布E增量后，按仓库既有目标优先在一个工作日内给限定复核结论或预计时间。实际工程阶段仍需E一次提交目标/修改范围/预期结果、原工程或副本选择和完整用户操作步骤；当前不提前申请或执行工程操作。

供用户转交E/W（本会话没有跨任务发送工具，未声称已送达）：请定位上表四类原件并回报Git身份，W只发布合同建议/测量方案/验证输入准备，给准确远端SHA；找不到则逐项如实纠正登记，不依据派工摘要声称已交付。

给A核对本次B文档的提示：固定本文件所在新提交，只核对两个新增文件的来源、候选一致/待决/工程证据分类与缺件边界；不要将其作为E完整包验收，不重做已批准工程测试。未来给B复核E包的提示由W填入E实际SHA、清单及日志后生成，不能复用本B文档提交号冒充E实现版本。
