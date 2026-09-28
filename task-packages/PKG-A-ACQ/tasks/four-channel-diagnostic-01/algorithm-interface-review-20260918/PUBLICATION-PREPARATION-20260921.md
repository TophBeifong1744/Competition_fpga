# E 准备材料：W 限定发布入口

## 2026-09-23 断点续作增量（覆盖下方旧接收状态）

- E最新明确交付范围为`E-PREPARATION-SHA256.json`中的12份原件，另包含清单本身；W已原样接收`E-HANDOFF-20260921.md`、诊断脚本、封包脚本和两次依赖诊断记录。原六份准备材料不改。完整性新增验证使用`seal_e_preparation.py --verify`。诊断脚本依赖A机F盘实际产物，不是跨机器可直接复跑；B可先核对归档diagnosis与准确Git对象，不因缺A机F盘声称失败或实板通过。W本轮未重跑现场产物诊断。
- 已收到B直接远端`task/member-b-h3-engineering-closeout-20260921`准确`696d21000adfb1b39332bb35c1ae7b45d2b75227`，新增两文件，无算法改动。入口：`task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/E-PREP-HANDOFF-20260921.md`。W已读取；其中WAIT_E_SOURCE_DELIVERY是B当时未收到E材料的状态，本次发布后应按新SHA复核，不能继续据该文字判E未生成。
- B的原集中意见对象`3c04a8c221a3808846e749c8814ad22a85e8e13d`现在可获取，E须结合上述696d210准确对照表核对候选一致/待决项；W接收不等于E已收到、B批准本包或双方冻结。实际跨任务工具仍不可用，由用户转交。
- E依赖诊断已确认：S1旧policy绑定旧check_entry原件，新活动检查器字节等于批准21c141b对象，非换行/损坏。建议保留安全修复、在原S1包新增限定适配；本包只有只读诊断和建议，无加载放行。C新八段仍按当前操作单，入口修复由E负责，不转派拓芙采录。
- 断点前准确提交`ae28d49e318ba31611d7fb9c28dd31af65e50f2d`的干净副本完整性检查通过。旧`publication-check.json`保留，因新增交付及属性/校验器变化，当前清单为`publication-check-final.json`，校验器默认只读检查最终清单。普通diff检查曾将冻结CRLF识别为尾空白，使用`core.whitespace=cr-at-eol`检查通过；原件未为消警告而换行重写。

以下为9/21初次接收记录，遇接收状态冲突以上述增量为准；原范围限制继续有效。

2026-09-21；已采用2026-09-17增量复核。作者E，发布W，独立复核B。本页只组织交付，不修改E实现或代签生产合同。

| 字段 | 本批记录 |
| --- | --- |
| 分支 / 基线 | `codex/toph/production-preparation-review-20260921`；main基线`704407e19f25a5405ef4d8f0272e977224e69b2c`；受审版本取本页所在发布提交完整SHA，由W远端回读后回报 |
| 申请 | 生产profile建议、16项服务测量计划、fixed4输入/整数期待准备；不是生产ABI冻结、RTL实现、实时或完整H3 |
| E原件范围 | `E-CONTINUE-20260921.md`、`prepare_production_delta.py`、`evidence/e-dispatch-20260921-run01/`四个JSON；逐字节保留 |
| W新增 | 本页、仅作用于本批的`.gitattributes`、`verify_preparation_publication.py`、`evidence/w-preparation-20260921-run01/`复跑及完整性清单；其他本机候选不纳入 |
| 依赖 | Python标准库、Git及完整对象`f08556d01821d6c3c8204fdac2c38f53b2107c05`中的`service-budget-20260921.json`；源码从固定Git对象取预算，不依赖兄弟未提交目录 |
| 实际运行 | 隔离工作树执行准备脚本退出0；145向量、8手算锚点、16余数类别、16服务身份；复跑向量和固定预算与E原件逐字节一致，result一致；command因目录不同不要求字节一致 |
| 复用 / 未测 | 已批准f085/ca512/ad30及旧FFT结论仅引用；不重复旧33/122/30项、FFT或耐久。无DUT逐码、AMD、ARM、实现、实板；16上界和总内存峰值仍未知，REALTIME_BLOCKED |
| B复核重点 | 表中数制域/epsilon参数绑定、完整状态集合/跳过条件、身份和TTL、8前视及停止/所有权建议；向量期待/覆盖合理性与测量计划边界。145项是准备向量，不是145项RTL测试 |

## 复跑（准确检出、仓库根、Python 3）

```powershell
$a='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918'
python -B "$a/verify_preparation_publication.py"
python -B "$a/prepare_production_delta.py" --out <不存在的新目录>
python -B "$a/verify_preparation_publication.py" --rerun <上述新目录>
```

清单见`evidence/w-preparation-20260921-run01/publication-check.json`；校验器只读。浅克隆缺固定Git对象须获取对应提交，不退回工作区预算。再次向已有输出运行会拒绝覆盖，保留原记录。

## 本页覆盖E旧录音安排，不改作者原件

E第5节“一段/不重录八段/只沿positioned-single-source”是旧派工时点，**现在不执行**。唯一现行安排是main基线中的`docs/phases/2026-09-13-to-10-01/c-recording-batch-20260921.md`：C全流程新八段，A接收、B独立诊断；新唯一批次，首段目标输入完整性检查通过后继续余段，不等B决定第二段，拓芙不代采/整理。该覆盖不是声学批准。

W读取了本机旧`batches/positioned-single-source-01/preflight-01/failure.json`：`trusted-direction-input-20260918/scripts/prepare.py`调用`background-target-stop-20260917/check_scene.py`，在`timerfixed-entry-01/check_entry.py`的依赖哈希检查拒绝。此文件未包含在本批，也不是B复跑本批准备脚本的依赖。E尚须按新旧准确批准对象核对加载入口依赖并回交正确入口或限定返修；W未改哈希、移除检查或执行Run。保持入口问题未关闭，不宣称C已接单/实录。

## 跨任务与批准状态

fetch及main直接远端核查为上述704407。dispatch所报B意见`3c04a8c221a3808846e749c8814ad22a85e8e13d`在本机Git对象中不存在，已刷新远端引用未包含；未取得`DISPATCH-20260921-B.md`原件，不能用旧接口包顶替。请B推送后回准确分支/SHA，W核实并交E集中对照；不因此阻止本准备包发布。

当前工具未提供跨任务发送入口。W通过用户转交复核提示词，不称已实际送达B/E；收到、技术同意及独立批准分别记录。待B限定批准才按范围合入main及batch-closeout；本次不合main、不清理任何工作树/分支。共享目录E原件及其他未完成材料保留，不强行清零。
