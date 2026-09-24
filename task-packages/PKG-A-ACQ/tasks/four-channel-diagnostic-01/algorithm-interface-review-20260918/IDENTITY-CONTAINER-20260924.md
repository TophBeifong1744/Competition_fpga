# D14-02：身份容器候选 v1

状态：`PROPOSED_BY_A / WAIT_B_CONFIRMATION`，不是生产配置。承接B对PR #30的`ec5017d`复核；本次为原D14-02文稿返修第1轮，不重置后续同因返修计数。

机器字段定义在同目录 `identity-container-v1.schema.json`，使用JSON Schema 2020-12。以下编码、引用解析和语义规则同为必需条件；只通过JSON Schema不能获得生产hash/准入结论。这里固定的是容器结构，尚未完成的外部算法对象不得以任意字典、假摘要或省略字段绕过。

## 输入、规范化与唯一字节

1. 输入必须是无BOM的合法UTF-8 JSON；允许无意义空白及等价JSON转义，不要求输入文本已canonical。先解析对象并拒绝任意层重复键（按解码后的键比较）、NaN/Infinity及非ASCII解码字符。所有数字码值/版本为字符串；v1容器没有原生JSON number或bool字段，不接受它们代替字符串。
2. 严格按对应kind schema校验对象及解析到的外部引用；执行下文语义/引用规则。草案可显示null，但不得进入通过路径。仅在数据、引用图及双方确认齐全时才允许生产身份生成；本轮机械探针即使算出了合成对象hash，也不是可下发身份。
3. 对象键递归按ASCII码字典序；数组顺序保持，尤其不能排序mic/pair。输出`{`/`}`/`[`/`]`/`:`/`,`，不插空白或尾LF；无BOM。字符串包在双引号中，逐个ASCII码输出：0x22→两个字节`5c 22`，0x5c→两个字节`5c 5c`；0x20..0x7e其余码原样输出（含`/`）；0x00..0x1f及0x7f仅输出六个ASCII字节的小写`\u00xx`，不使用`\b`/`\t`/`\n`/`\f`/`\r`等短形式。不得用`\u0041`替代`A`。这同时适用于键与字符串值；具体字段schema可以拒绝控制字符。
4. canonical payload为上述字节的UTF-8编码。身份为`SHA256(prefix || payload)`；prefix精确为ASCII `SoundSight/` + kind + `/v1` + **一个0x0a**，kind只能是`config`、`geometry`、`numeric`。展示为64位小写hex，C桥为32字节原值，禁止全零占位。
5. 规范整数串：零仅`0`，其余为无前导零的十进制，可负字段才允许一个`-`；无`+`、空白、小数、指数及`-0`。版本常量为`"1"`。schema限定通道/数组/枚举/位串长度；坐标有理数的分子属于整数Z，分母属于正整数，均不靠机器float处理。
6. 有理数仅有`numerator`、`denominator`两个字符串字段，gcd(abs(n),d)=1，零必须0/1。正有理数另要求n>0。约分和关系检验是schema后的必需语义检查，不得把schema正则通过当作已约分。几何坐标采用任意精确有限有理毫米值，声速采用正有理毫米/秒；不以此声明任何坐标已测准。

`{"name":"A"}`与`{"name":"\u0041"}`只是编码反例，均须生成同一canonical字节`{"name":"A"}`；它们不是本schema允许的生产config。输入必须解析后重新编码，不直接hash原JSON文件。拒绝非canonical生产输出时，应比较原输出字节与唯一encoder输出，不用语义相等代替字节相等。

## 三类容器：无可选字段、无扩展槽

所有下列字段均required；**v1无optional字段，任何null、遗漏或未知字段均拒绝**。每层对象均`additionalProperties=false`；schema自身的`$defs`不是实例字段。字段名区分大小写。

共同字段：`schema="ss-identity-container-v1"`、`version="1"`、`kind`为对应单一枚举。

| kind | 除共同字段外的完整字段 | 精确类型/含义 |
| --- | --- | --- |
| geometry | `scope`, `coordinate_unit`, `speed_unit`, `reference_mic`, `x_axis`, `y_axis`, `angle_convention`, `mics`, `speed_of_sound` | scope=`four-mic-planar-design`，单位=`mm`/`mm-per-second`，参考=`mic0`，轴=`mic0-to-mic1`/`mic0-to-mic3`，角定义=`atan2-y-x-degrees`。mics恰4项，按channel0..3顺序，每项仅channel、mic_id、x、y、z；channel与mic_id分别固定0/mic0至3/mic3；xyz为上述有理数，声速为正有理数 |
| numeric | `profile_id`, `geometry_sha256`, `twiddle_backend`, `algorithm_ref`, `source_manifest_ref` | profile_id为1..96位小写字母/数字/连字符（首位字母或数字）；geometry摘要非零64hex；backend仅`portable-q30`或`amd24`；两ref分别要求具名`ss-numeric-algorithm-v1`及`ss-numeric-source-manifest-v1`对象 |
| config | `geometry_sha256`, `numeric_sha256`, `acquisition`, `transport`, `activity_ref`, `calibration_ref`, `tracker_ref`, `ttl_ref`, `required_units_ref`, `timebase_ref` | 两摘要均非零64hex；acquisition与transport完整字段见下表；六ref的schema_id分别固定为`ss-activity-v1`/`ss-calibration-v1`/`ss-tracker-v1`/`ss-ttl-v1`/`ss-required-units-v1`/`ss-timebase-v1` |

| 子对象 | 完整字段（全部required，禁止额外字段） |
| --- | --- |
| acquisition | `sample_rate_hz="48000"`, `frame_length="1024"`, `hop="512"`, `channels="4"`, `row_words="8"`, `format="h1-0.3-s24-signext-le32"`, `capture_contract_ref`（schema_id=`ss-capture-contract-v1`）。这些是当前候选配置值，不是实际测频或真实设备身份 |
| transport | `worker="single-owner"`, `isr="enqueue-only"`, `rx_release="after-successful-copy"`, `token="session-generation-slot"`, `session="boot-scoped-monotone-u64"`, `generation="object-lifetime-monotone-u64"`, `binding_ref`（schema_id=`ss-transport-binding-v1`）。这里绑定逻辑政策，不虚构MMIO/DDR/缓存参数 |
| 任一ref | 恰5个字段：`schema_id`（上述对应常量），`schema_version="1"`, `schema_sha256`（规范schema文件原字节SHA256），`encoding="ss-canonical-json-v1"`, `content_sha256`（对应数据文件canonical字节SHA256，**此ref摘要不加三种根身份的域前缀**）。两个摘要非零64hex，无路径或任意扩展字典 |

geometry中mic0坐标须为(0,0,0)，四mic的z须为0，mic1满足x>0/y=0，mic3满足x=0/y>0；三点使坐标轴可定义。这些是schema后的关系检查，非某组实际40mm坐标的赋值。numeric引用的geometry须与config引用相同，backend/算法参数/源码清单必须一致；其余适用域由B完成算法对象时确认。

## 引用有向图与golden

箭头表示“hash/验证所依赖的对象”，必须无环：

```text
config -> geometry
config -> numeric -> geometry
numeric -> algorithm_ref, source_manifest_ref -> 不含根身份的规范源/ROM叶节点
config -> capture/activity/calibration/tracker/ttl/required_units/timebase/transport对象
验证绑定记录 -> config, numeric, geometry, 输入字节对象, golden字节对象
部署绑定记录 -> config, numeric, geometry, XCI/wrapper/ELF/工具与实际工件
```

根numeric不包含golden摘要，外部algorithm/source_manifest及其他上游配置对象也不得通过传递引用回到任何根身份、验证绑定或部署绑定。实现须遍历全部具名引用并检测环/缺节点，而非只看根三条边；每个外部schema必须列出其引用字段，无可扩展的不透明引用通道。三份根payload不包含自身hash或提交SHA，发布提交/审批证据在外部记录，避免自引用。

外部golden验证绑定是证据记录，不回流numeric身份。它须同时绑定numeric/config摘要、对应schema版本、输入原字节摘要，以及预期输出的具体文件/每项字节摘要、比较语义和来源提交。已有golden若内含numeric摘要，就保留全文件字节身份，从验证记录指向它；**禁止把该全文件摘要反向塞进numeric，禁止临时忽略字段或修改旧golden来破环**。本轮不生成这一尚缺真实输入的生产绑定记录。

源/ROM叶节点应明确精确Git导出blob或明确的原字节artifact；两者不静默混用CRLF。可加载XCI/ELF等与三份身份的关系放在下游部署绑定，避免工件内嵌config时config又hash工件的循环。

## 仍需B提供的具体对象，不填假默认

| 对象/schema_id | B需集中确认的字段语义及准确来源 | A负责的后续约束 |
| --- | --- | --- |
| ss-numeric-algorithm-v1 | D14-01逐节点格式/尺度/RNE/非法域、两类窗、PHAT参数、pair映射、CORDIC/DAS及实际适用域；区分候选方向同意与每个常量批准 | 完整字段schema、引用闭包及逐级实现绑定；不凭容器通过冻结算法 |
| ss-numeric-source-manifest-v1 | portable/AMD各自参考源码和ROM具体字节对象；对应golden验证绑定的目标身份 | 叶节点无反向引用，工具/XCI/部署身份另列 |
| ss-activity-v1 / ss-calibration-v1 | activity band/阈值/状态更新、标定数据与计算参数，确认生产参考及其适用条件 | 不能整拷开发config或默认采用9/22背景 |
| ss-tracker-v1 / ss-ttl-v1 | 状态/捕获/HOLD政策、TTL数值、单位、来源域和消费域；无error畸形事件策略关联I14-TOKEN-01 | 实际时间锚、溢出/unknown处理与接口实现；不默认512 |
| ss-required-units-v1 | 确切实例列表、pair映射、合法SKIPPED条件/原因及结果语义 | 运输unit和聚合/重复/漏项/晚错约束 |
| ss-capture-contract-v1 / ss-timebase-v1 / ss-transport-binding-v1 | B确认与输入/算法时间及配置语义兼容 | A起草采样来源/boot/session/interval锚、缓存/队列/错误归属与停止协议；实际地址/上界仍缺 |

上述外部schema尚未发布，故`schema_sha256/content_sha256`没有可下发的真实全集。它们是显式阻断，不是可由实现者自由填写的扩展点。JSON Schema只检验容器结构；生产接入还必须成功解析并验证所有外部schema/内容、语义关系、无环图、实际来源及双方对同版的确认。任何一个缺项都保持`WAIT_B_CONFIRMATION / production_frozen=false`。本轮不部署生成器或改现C ABI。
