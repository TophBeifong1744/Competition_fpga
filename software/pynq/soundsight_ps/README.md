# SoundSight PS offline core 0.1.0

本包是可调用的标准库离线软件核心。Python 3.10+，从仓库 `software/pynq` 运行 `python -m soundsight_ps`，无需安装、PYTHONPATH 或 PYNQ/NumPy。真实 CPU 地址、适配器、镜像、cache/allocator/abort 合同仍为 UNBOUND；`hardware` 始终拒绝，不调用 Overlay、MMIO、下载、复位或运动。

本包没有算法、生产时限默认值或板型默认值，也没有修改 #22 mock-only 核心或 probe。其 simple S2MM、noDRE 按 memory 宽度对齐、异常保留所有权和授权 abort 原则作为独立软件规则复用。独立测试由后续串行批次执行；源码作者仅允许 import smoke，不把测试脚本输出作为硬件证据。

## CLI 与退出码

```powershell
Set-Location <repository>/software/pynq
python -B -m soundsight_ps inspect --profile <profile.json> --artifact-root <input-root> --out <new-output>
python -B -m soundsight_ps decode --profile <profile.json> --artifact-root <input-root> --raw <capture.bin> --out <new-output>
python -B -m soundsight_ps replay --profile <profile.json> --artifact-root <input-root> --script <script.json> --out <new-output>
python -B -m soundsight_ps hardware --out <new-output>
```

`--out` 必须不存在；已有证据拒绝覆盖。输入只读，输出含输入前后路径/长度/SHA256、`audit.jsonl`、只创建一次的 raw/JSON sidecar 和 `result.json`；失败和缓冲处置保留。0 表示指定离线命令完成，2 配置/协议/中断失败，3 硬件拒绝，4 内部或证据 I/O 失败。argparse 的用法错误为2，尚未创建证据目录。所有结果含 `hardware=NOT_RUN`、`acceptance=NOT_CLAIMED`，绝不称硬件 PASS。

inspect 核静态文件 hash、类型扩展名、相对路径/链接/根边界、bit/HWH同目录同名、共同 build_id 声明。它不解析厂商工件、不证明 part/IP/address 或 bit/HWH 的实际内部匹配；manifest 内容/加载/回读身份留给真实适配批次。非空 artifacts 必须同时声明 bit、hwh、manifest；test-only 的空数组被明确允许，不制造合成工件充实板输入。

## 完整 profile schema 1

以下所有键必填，未知键拒绝。例中整数、地址和期限仅是可编辑的模拟参数，不能用于板端。scope 只能为 `SYNTHETIC_TEST`，transport 只能为 `TEST_TRANSPORT`。profile 经解析后通过 `.data` 返回副本。

```json
{
  "schema_version": 1,
  "scope": "SYNTHETIC_TEST",
  "transport": "TEST_TRANSPORT",
  "raw_schema": "raw32-le-s24-v1",
  "boot": 7,
  "epoch": 11,
  "generation": 13,
  "deadlines": {
    "domain": "SYNTHETIC_TICK", "unit": "ticks",
    "poll": 5, "arm": 20, "transfer": 100,
    "stop": 200, "abort": 200, "archive": 5
  },
  "dma": {
    "mode": "simple", "s2mm": true, "mm2s": false,
    "sg": false, "dre": false,
    "memory_width_bits": 64, "axis_width_bits": 32,
    "length_width_bits": 14, "length_granularity": 32,
    "cache_line_bytes": 64, "packet_bytes": 32,
    "slots": [{"name": "rx0", "address": 4096, "capacity": 64}]
  },
  "queue_limit": 64,
  "artifacts": [],
  "declarations": {
    "part": "UNBOUND", "image_identity": "UNBOUND",
    "cpu_wire_schema": "UNBOUND", "ps_time_bound": "UNKNOWN"
  }
}
```

boot/epoch/generation 为 uint64；session 是每实例独有的 host UUID，transaction 为递增 uint64。它们与原 source_id 分开。内存地址/容量为显式模拟描述；地址按 memory_width_bits/8 和 cache_line_bytes 对齐，容量覆盖包且为 cache-line 倍数；槽区间无重叠/uint64溢出。packet_bytes 非零、32B整数倍、满足 length_granularity 和 `(1<<length_width_bits)-1`。一次只允许一个活动 S2MM。初次和重启分配都需 `allocate` 事件。

artifacts 的每个对象准确包含 `kind,path,bytes,sha256,build_id`；kind 为 bit/hwh/manifest/xsa/dtbo/ltx，path 是 artifact-root 内无链接相对路径，manifest 扩展名 .json，其他为对应后缀，kind/path不得重复。bytes为正整数，sha256与原字节一致。part/image 字段仅声明，不授准入。

poll/arm/transfer/stop/abort/archive 均为必填正整数。每个 transcript 调用的 tick 增量受对应时限约束；prepare→arm→首RUN的总增量受arm限，arm后完成轮询受transfer限，STOP和abort含清理总增量分别受stop/abort限。每事件tick必须严格增长，events/actions数量受max_events限，因而不会无限轮询。`archive` 事件约束合成边界；真实磁盘 fsync/CPU调度和PS时钟实时上界为 UNKNOWN，模拟tick不证明Linux时限。实际参数域若超出本schema，应冻结新合同版本，不把秒数换进tick字段。

## raw 数据和 native 边界

原采集契约 `raw32-le-s24-v1`：每32B为8个LE32字，顺序 id_lo、id_hi、mic0..3、clip_flags、reserved。mic必须已符号扩展的 signed24-in-int32，范围 -8388608..8388607；低4 clip位分别对应4麦，其他flags位和reserved必须0。uint64 source_id = lo | hi<<32。原bytes先归档，整数导出不归一化、不填零、不重编号；clip不当drop。重复/倒退ID拒绝，gap保留并审计，gap的drop语义为UNKNOWN。跨正常STOP/restart仍保留 prior raw ID，不能因新epoch掩盖旧ID。

C固定版本 `b529fed84bde1d5d5d6326e0d8870416c738657a` 的同域 native 字段与未来CPU wire schema分开：

| kind | fields | 当前范围 |
|---|---|---|
| result | valid/abort/eligible(bool)、identity(U725)、angle_q8(S18Q8)、angle_deg(U9) | 原native事件观察；不推导CPU held/ACK |
| diagnostic_word | bank(U3限定0..4)、sequence(U64)、word/words(U6)、last(bool)、data(U32) | 保留37/41/38/27/32 words；逐bank/sequence按word顺序 |

测试record必须准确含 `envelope="SYNTHETIC_TEST/TEST_TRANSPORT"`, `native_version=<完整C SHA>`, `kind`, `fields`。diagnostic长度/last核真实合同；result保留完整725位identity，不把其拆分成未经批准CPU结构。`OpaqueCpuRecord(schema_id,adapter_version,payload:bytes)` 和 `CpuRecordAdapter`/`CpuControlAdapter` 是未来版本绑定接口，实际实现缺失。

C top 实际raw AXIS只在内部，tready固定1；report/abort ready固定1，result为瞬时别名；没有当前CPU held result ACK/sequence。C诊断consumer是逐word valid/ready→ACK，不是CPU buffer。测试native的 host `record_id`、归档ACK义务和`ack_native`是 **TEST_TRANSPORT_HOST_JOURNAL_ONLY**，不宣称C已经提供CPU队列或ACK寄存器。

`NativeCommand` 只验证当前CONFIG/RUN/STOP/RECOVER同域操作、context160、map96 reserved[95:83]=0、1..8388608 native周期数；不替代原RTL完整map/配置/运行资格检查。native周期数与SYNTHETIC_TICK/PS时间分开。本核心不发NativeCommand、没有运动arm或enable路径。

## API 与生命周期

```python
from soundsight_ps import Profile, Session
from soundsight_ps.dma_rx import TestTransport
from soundsight_ps.evidence import Evidence

profile = Profile.parse(profile_object)
transport = TestTransport(script_object)
session = Session(profile, transport, Evidence(new_output_directory))
# 按下述显式脚本调用start/submit/complete/consume_native/stop/restart/abort/close。
```

start要求新session，模拟分配每槽及新鲜clean/drained、无pending_packets/owed_records。它只进入逻辑RUNNING；submit得到新fresh完整包credit，prepare_rx缓存准备/屏障，**arm前**置DMA_MAY_OWN，再arm确认、首个实际模拟RX arm后run。测试credits可以在首run前由脚本声明，不能据此推导真实PL启动/credit来源。没有额外空DMA。

complete有限轮询本session/epoch/generation/transaction的新sample_sequence；done与exact actual_length为必要条件，IOC单独不足。随后必须逐buffer、新匹配identity、所有writer退休和barrier证明；invalidate+barrier后CPU read；原bytes归档/readback成功，整数验证/export成功才回FREE。顺序严格串行，另一槽不同时arm。FREE循环利用不意味着allocator释放。stop最终释放allocator槽还要新退休证明和不可变处置归档。

stop显式请求source停止，保留active并排空；status有真实pending_packets才申请新credit/挂完整DMA，有owed_records才读测试native；source clean/drained、无active/ACK义务/未完diagnostic才退休释放各槽。没有empty DMA、fake EOF、reset或清sticky错误假设。restart仅在clean STOPPED、所有槽RELEASED且无义务时递增epoch/generation，明确allocate，并核新clean status。历史、首错、原帧号、native重复证据从不删除。

异常/partial arm/KeyboardInterrupt保存first_error和当前slot disposition，转FAULTED；不再submit、CPUread、正常native消费或正常release。显式 `abort(authorized=True)` 才进入处理：保存pre_abort→abort请求→本交易新匹配全writer静止/source_stopped/零owed证明→每槽新退休→仅归档处置（不读异常payload）→释放。ABORTED仍保留首错，不能正常restart。quiescence里返回的后续error仅保留，不覆盖首因。未知ownership保持pin和resource claim；RELEASE_UNKNOWN不双release、不静默reset/retry。close只接受全释放STOPPED/ABORTED并解除owner。

每资源resource_id在同进程只能由一个session占有。RLock和重入检查保护公开状态变更；它不是跨进程kernel ownership证明。SIGKILL、进程退出后的真实pin/连续物理内存、cache一致性、IRQ race和DMA恢复均需真实driver；Python强引用/try-finally不证明安全。当前没有IRQ路径；IOC仅测试观察，没有虚构W1C或IRQ清除顺序。

## TestTransport script 精确形状

script必填 `schema_version=1,scope="SYNTHETIC_TEST",transport="TEST_TRANSPORT",resource_id(非空文本),max_events(正整数),events(list),actions(list)`。actions为 `{"op":"start|complete|native|stop|restart|close"}`，或 `{"op":"submit","slot":"rx0"}`，或 `{"op":"abort","authorized":true}`。未知键/参数拒绝。replay通过Session实际API执行；失败后只允许显式abort/close，且曾失败的执行最终exit2，成功恢复不抹失败。内部异常exit4仍保留session处置。

每event准确含 op,tick，以及 reply 或 error 二选一，可选expect。expect为实际调用参数的子集比较。`error`是非空消息，`"KeyboardInterrupt"`注入中断，其余注入ProtocolError。op必须匹配下一调用；不自动补观察或跳过失败。`"$current"`递归展开为当前调用完整identity `{boot,session,epoch,generation,transaction}`，可故意用显式旧identity制造反例。sample_sequence为整个session严格递增的非负整数，跨epoch也不清零。

| event op | exact reply keys/value | 参数/identity |
|---|---|---|
| allocate | allocated:true | slot/address/capacity；tx0 |
| status | identity,sample_sequence,clean(bool),drained(bool),pending_packets,owed_records,error(null) | tx0；两计数0..queue_limit |
| credit | identity,sample_sequence,credit_id,packet_bytes | 新tx；同epoch credit_id不能复用 |
| prepare_rx | cache_prepared:true,barrier:true | slot/address/capacity；新tx |
| arm | armed:true | slot/address/length/credit_id；新tx |
| run | enabled:true | tx0；仅首RX arm后 |
| completion | identity,sample_sequence,done(bool),ioc(bool),actual_length,error(null) | slot；活动tx |
| retired | identity,sample_sequence,slot,buffer_retired:true,all_writers_retired:true,barrier:true | slot；对应slot最后tx，未用槽tx0 |
| invalidate | invalidated:true,barrier:true | slot；活动tx |
| read | data_hex(实际完整包hex) | slot；活动tx |
| archive | permitted:true | label/bytes；raw/整数为slot tx，native为tx0 |
| native | identity,sample_sequence,record_id,record | tx0；record为上述native测试封装 |
| ack_native | acked:true | record_id/record；tx0，host-journal测试ACK |
| stop | stop_requested:true | tx0 |
| abort | abort_requested:true | 有active为活动tx，否则tx0 |
| quiescence | identity,sample_sequence,all_writers_retired:true,source_stopped:true,owed_records:0,error | abort identity；error为观测诊断可保留 |
| release | released:true | slot；最后slot tx |

以下是**仅干净空会话的模拟脚本示例**，没有raw capture或硬件事实。与上面的单槽profile配合即可由独立执行者调用replay。产品没有生成测试资产文件。

```json
{
  "schema_version": 1, "scope": "SYNTHETIC_TEST", "transport": "TEST_TRANSPORT",
  "resource_id": "example-fixture-only", "max_events": 20,
  "actions": [{"op":"start"}, {"op":"stop"}, {"op":"close"}],
  "events": [
    {"op":"allocate", "tick":1, "reply":{"allocated":true}},
    {"op":"status", "tick":2, "reply":{"identity":"$current","sample_sequence":1,"clean":true,"drained":true,"pending_packets":0,"owed_records":0,"error":null}},
    {"op":"stop", "tick":3, "reply":{"stop_requested":true}},
    {"op":"status", "tick":4, "reply":{"identity":"$current","sample_sequence":2,"clean":true,"drained":true,"pending_packets":0,"owed_records":0,"error":null}},
    {"op":"retired", "tick":5, "reply":{"identity":"$current","sample_sequence":3,"slot":"rx0","buffer_retired":true,"all_writers_retired":true,"barrier":true}},
    {"op":"archive", "tick":6, "reply":{"permitted":true}},
    {"op":"release", "tick":7, "reply":{"released":true}}
  ]
}
```

capture脚本在start之后加入submit/complete动作及credit→prepare_rx→arm→首run→completion(可多次)→retired→invalidate→read→archive(raw)→archive(integer-export)事件，随后stop序列。实际raw_hex由输入原件/独立测试资产提供；产品不生成golden、padding或假的source ID。negative脚本可直接替换任意观察/注入error，并明确追加abort/quiescence/retired/archive/release；缺证据时预期仍pin。

## 后续硬件配套和人工保存点

当前产物身份是软件源码冻结清单；bit/HWH/image/runtime与软件的匹配记录仍缺失。下一接合由A/E1提供实际CPU bridge/schema、raw S2MM连接、held result快照/队列策略，C提供板/image/allocator/cache/abort版本；实际part -1/-2差异由A/C确认。建议先明确最小一致性bridge和串行单S2MM perbuffer退休证明，再绑定版本；本包不替人作器件、地址或cache选择。

本Python批次无需Vitis工程或ILA新增。若真实平台交付包含Vitis/XSA复现，由人用匹配XSA建/打开该平台并保存版本、硬件build_id、BSP/driver配置及native build log；本批Vitis操作NOT_RUN。现场获授权人员另行加载准确bit/HWH，保存实际Overlay/runtime identity、命令/exit、raw/状态、pre-abort和缓冲处置。复用C现有同61.44MHz ILA的STOP/故障/恢复、来源valid/ready/TLAST、result identity和diag逐word观测；核bit/LTX匹配、真实探针/时钟/触发/窗口。截图可帮助定位，原生日志/报告/raw是可复核原件。必要资源、routed timing、实物安全未齐时不启动硬件。本包不宣称板端接通或整机验收。
