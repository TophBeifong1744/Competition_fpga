# 累计B声学诊断包：发布与A复核唯一入口

本次发布task/member-b-acoustic-mechanism-01，沿fd1b99c已有基线累计提交；准确待审SHA由工作执行在推送后提供。不合入main，不申请默认算法替换或完整H3通过。

## 和原复核提示词的关系

acquisition-breaks/TO-A.md包含在本包中，是累计诊断的原复核提示词，不是另一项独立交付。本入口补充其后收到的A输入依据回复，保留旧文件原样：其中“请回复通道映射/固定延迟材料”的请求已由a-input-response/README.md收口，不要求A再回答。A资料回复不等于B算法研究已获复核通过。

## 给A的当前复核提示词

请以工作执行提供的准确远端SHA复核本累计诊断包，先读本文件及acquisition-breaks/README.md、joint-full-replay/README.md、a-input-response/README.md。

申请范围：既有八段开发实录上的声学机制诊断源码、复现证据、失败与负结果入库。没有新录音，包含实录派生逐帧方向、相关/频谱特征、状态和来源元数据。默认PHAT和跟踪器未改。不要将材料归档批准写成稳定锁定、独立性能、校准、实板、实时或完整H3通过。

核心结论：联合取峰增加几何有效帧，但八段4488帧仍全部0 fresh，最高捕获计数3；背景数值有效700→974但活动门0放行。目标200ms候选区440帧，门前有效202→332，新增131损失1。原/联合可捕获帧137/267，方向分散重启27/102，范围外打断27/88；不能把事件数直接当不同尝试数下的失败率。

请按复核效率规则复跑完整回放和捕获归因，并核对输入/依赖SHA、4488帧旧基线与跟踪状态、191帧原联合结果。其他研究按必要性抽查，不重跑未受影响的旧定点/FFT研究。核对phase-confidence中失效run01与最终portable02的明确区分，保留TAU_BOUND误用及其他失败记录。峰宽截断、强制闭合、同批开发/偏置选样、名义角度非真值等限制不可省略。

A已说明没有独立声学映射和固定延迟/相位/增益参数；数字同步有RTL依据，不等于声学校准。B已核对指定Git版本、八段主机bit/ELF绑定及主机WAV哈希。请评审B对这些依据的引用是否准确，不重复补资料请求，不追加C录音或默认归因硬件。

复核通过后仅由复核人按批准范围合入；若发现阻断请给准确路径、复现命令及首错。所有命令在相应README中，输出使用全新目录，不覆盖冻结证据。

## 主要复现入口（仓库根）

```powershell
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/acoustic-mechanism-20260921/joint-full-replay/run.py --repo . --out F:/NUEC/validation/a-joint-full-review-01
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/acoustic-mechanism-20260921/acquisition-breaks/analyze.py --repo . --out F:/NUEC/validation/a-acquisition-review-01
python -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/acoustic-mechanism-20260921/a-input-response/verify.py
```

可将输出路径换为A可写的新目录。Python3.12.14、NumPy2.3.5为作者环境；A独立环境的复现未在本次发布中冒称通过。捕获归因读取绑定的归档时间线，完整回放另行输出；两者作用不同，不能只跑归因就声称全链复现。
