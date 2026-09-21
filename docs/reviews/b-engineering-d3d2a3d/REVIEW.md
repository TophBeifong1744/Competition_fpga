# B H3 工程收口增量复核：需修改

实际复核日期2026-09-21，A独立执行。**本轮不批准整包合入：两个轨迹检查缺口需返修；以下已经检查的数值、预算及既有通过部分可在增量复核中复用。** 不是完整H3的新门槛，不重派E01～03，不修改B实现。

## 准确身份与范围

- 固定实现提交：`d3d2a3d4e78932830bf12bd84c0517b0a2092872`；独立工作树 `git rev-parse HEAD` 确认为该完整SHA。
- 直接远端任务分支在检查时为 `dbd7ab5b35c75dfe9779a0452643d4bd2df24657`，相对上述实现仅更新 A-REVIEW-PROMPT.md 与 DELIVERY.md（7增1删），没有把移动分支头当实现批准对象。
- main基线 `cf026cf29518488f8c7275b825f3487a8d892f80`；基线到实现候选没有本子目录之外的改动。既有e473824仅声学离线批准，其余关闭项范围保持；本轮未重审旧FFT/声学/事务包。
- 包路径：`task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/`，以下源码行号相对此目录。
- 环境：A的Windows/Intel、CPython3.12.14、NumPy2.3.5；以局部core.autocrlf=false独立检出原字节，未改共享分支、B工作树、全局Git配置、one/Vitis工程或A/C原件。

## 实际运行

下列P代表上述包路径；cwd为准确提交独立副本根，OUT是此前不存在的外部路径。

```text
python -B P/run_all.py --repo . --out OUT
python -B P/check_delivery.py --repo . --out NEW_CHECK.json
python -B <A-review>/probe.py --repo . --out NEW_PROBES
python -B <A-review>/compare.py --repo . --run OUT --out NEW_COMPARISON.json
```

前两入口分别退出0；run_all三阶段均0。check_delivery核验28输出、7源码、14本地链接及FG/D依赖。命令与环境路径原记录见evidence/runner.json；输出/日志在evidence/，独立反例在probes/，交付核查在delivery.json、比较在comparison.json。独立探针退出0表示探针执行成功，**不代表错误轨迹被正确拒绝**，实际两例误接收如下。

1215向量最大候选误差0.5077271740956348个Q8码；旧942反例、最大2530码保留。非法输入6、RNE162、饱和6、动态极端32输出及作者14种轨迹反例均在A环境实际通过。与run05比较15027个严格叶值相同，物理浮点字段差异0；checks目录各JSON字节结果逐项见comparison.json。预算语义相同。runner路径、cwd是环境数据，未要求跨机文件字节相等；没有重写冻结输出或放宽原阈值。

## 需修改项（本包检查器范围内）

### R1 / P2：available没有绑定完成状态的最早可见时刻

位置：`trace_scoreboard.py:99–100`；状态处理在84–96行。

独立反例 `probes/available_before_final_status.json`：仅将正常夹具commit.available从2改为0；最后一个ifft状态仍在now=2到达，检查器仍返回TRACE_MATCHES_CANDIDATE_ONLY、commits=1、accepted=32。当前只检查 `available <= now <= expiry`，未记录或约束最终必需状态的可见时间，无法检出提前声明结果可用。FLOW关于“完成状态可见时刻、不得倒填帧尾”的约束没有被该检查实现；不能用这份PASS确认available真实性。

修改要求：明确commit.available的身份（不是源采样编号或帧尾），在独立完成集合全部到齐后形成最早可见时刻下界；至少检查 `all_required_status_visible_at <= available <= commit_now`。如果它还代表后级完成，应补独立后级状态，而非由DUT自报可用时间。保留允许提交晚于完成的合法路径，不简单强制所有available等于commit_now；加入提前available拒绝、同拍完成允许、延迟提交允许及过期拒绝。若意图仅检查自报时间上界，须显式收窄合同/结果名称，不能宣称已验证可靠available。

### R2 / P2：采样身份字段缺严格整数类型检查

位置：`trace_scoreboard.py:118–119`；背压比较在112–113行。

独立反例 `probes/float_sample_identity.json`：把emit=8的source_sample改成0.0、available改成8.0，仍返回通过。Python数值相等会把float与int视作相同，bool同理；仅值相等不足以验证合同要求的整数时间/编号，背压payload等值比较也不能代替schema检查。

修改要求：source_sample显式检查整数类型（排除bool），本离线profile允许startup的-8..-1，之后按emit-8；available用严格uint64检查，所有有效/被背压拍都先验证schema。增加float、bool、边界越界以及背压期间类型变化反例。不要误把startup负编号改成uint64或更改原PCM。

外部expected_units对删减完成集合、以及背压PCM变化，A独立控制反例均被正确拒绝。这两项不需要重做，返修集中在R1/R2和邻接边界。

## 集中裁决与下一步边界

1. **CORDIC需要独立数值profile。** 共同精确左移和+180→−180规范化都会改变输出，应给新候选独立profile/config hash/golden，旧FG及reference25保持。可继续作为离线候选，不能本轮直接替换生产。A用展开乘积的Fraction包含界独立算得ceil=80001531，低于B的80001546，二者均小于2^27，因此S28保守容器合理；这是所有合法S23输入归一化后的包含界，不是最小位宽或全域≤1码误差定理。LZC、先扩宽取负/移位、旧角累加S26及最终规范化必须纳入后续硬件合同。
2. **8前视/17历史接受为下一步候选接口参数。** 对±8样点域，不读取零权重邻点时覆盖emit−16到emit；不倒签旧9前视实现。启动零、真实EOF补尾与gap/reset分别处理。串行最多两beam加一个最新pending可继续作为资源受限候选；接受“请求可被更新覆盖、最坏960样点/20ms平滑回mono”的研究取舍，尚未批准生产部署，也不等价旧立即重定向。
3. **统一session采样时基，硬停与平滑停止分开。** session/interval内采用整数物理采样计数；source_sample、emit、available各有独立含义和明确映射。ready停顿不暂停TTL，HOLD不续租；同拍fresh/expiry沿既有候选顺序；reset/fatal优先于commit/output，旧epoch回调只审计。音频平滑STOP不得充当紧急停止：另立fatal/session_abort类硬停语义，取消在途未消费输出/方向；已消费PCM不能撤销。真实CDC/异步同时性/设备中止尚未验证。
4. **ROM首选评估PS DDR驻留。** 552960B为净载荷，不含NPY头，不能默认整块塞入PL；先绑定ROM/profile SHA、规范角域、地址区间、所有权/cache和按请求取数，再评估有限控制传输。此处是后续部署方向建议，不是地址/板卡工程选择或PYNQ准入批准。压缩/PL缓存若另选，另审内容与最坏访问时间。
5. **有限服务仍REALTIME_BLOCKED。** 下一步A在用户选择实际one/Vitis工程后给出准确核/IP/profile、时钟域、配置/排空/最终status上界、RAM端口/仲裁、sqrt/除法器服务和输出最大blackout/持续服务率。B据这些输入重算总服务与队列，不重派旧节点。103364只为8FFT+6IFFT历史槽算术，不能当WCET；portable Q30与AMD24 golden独立。107496B历史列举、202816B逻辑布局、552960B净ROM不同口径，不能混加。未知上界继续null，不能凭有限队列或10.6667ms hop批准实时。

## 复用、未测、批准边界与处置

可复用本次已检查的CORDIC确定向量、S28包含界、RNE/饱和/极端PCM、依赖身份、预算分账及已正确拒绝的反例；这不单独构成生产profile批准。整包状态NEEDS_FIX，R1/R2修复后按准确新SHA增量检查，不重复未受影响的1215向量或旧H3研究，除非实现/合同/依赖随修复改变。

未运行完整FFT/IFFT、AMD、RTL、Vivado/Vitis、板测、实时或声学研究。轨迹只是数学夹具，不是生产事务、DUT ready、全14变换完成集合或真实采样时钟证明。没有批准完整H3、生产接口/数制/资源冻结、声学收益或实板。

本轮没有合并或推送候选，main未改；没有删除分支、工作树、输出、旧失败或独有证据。A报告、探针及实跑输出在本复核目录，原外部运行副本也按用户要求保留。待审分支保留供B返修；不夹带后续文档头为实现批准。
