# B 声学机制增量：限定复核通过

审核日期：2026-09-21。准确审核版本 `e473824a27adce51d38fddc19961e0b965ac5886`，直接远端 `task/member-b-acoustic-mechanism-01` 已核对。审核开始时共享 HEAD/远端 main 为 `db549b55f134d2b9dbfa5baef7d1ec19e288664b`；研究依赖基线 `fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd`。既有定点、动态 DAS、R1/R2 批准不扩大，本轮不重审它们。

结论：**通过限定复核，只批准离线诊断材料与复现证据入库；不采用联合候选，不代表锁定问题解决。** 本轮无技术入库阻断。

## 身份、环境与命令

在新独立 detached worktree 固定上述 SHA，用局部 `-c core.autocrlf=false` 检出，没有修改全局配置、B 工作树或冻结证据。A 环境为 Windows 11 / Intel i9-14900HX、CPython 3.12.14、NumPy 2.3.5，不依赖 AMD DLL。以下 `P` 为 `task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/acoustic-mechanism-20260921`，cwd 为准确审核副本根；`OUT` 为新建外部目录，Python 均使用 `-B`。

| 实际命令（展开 P/OUT 后执行） | 结果 |
|---|---|
| `python -B P/joint-full-replay/run.py --repo . --out OUT/full` | 0；4488 帧原基线/跟踪一致，191 个旧联合结果检查通过 |
| `python -B P/acquisition-breaks/analyze.py --repo . --out OUT/breaks` | 0；逐事件分类、分母与中断计数通过 |
| `python -B P/a-input-response/verify.py` | 0；历史 Git blob、8 份 metadata/version-binding、播放 WAV 依据通过 |
| `python -B -m unittest discover -s P/<目录> -p test_*.py -v` | acquisition-breaks 3、lag-boundary 3、peak-shape 4、joint-arrival 4、direction-ambiguity 4、phase-confidence 4、pair-consistency 5、background-excess 4，共 31 项通过 |
| `python -B P/<目录>/analyze.py --repo . --out OUT/<目录>` | lag-boundary、peak-shape、joint-arrival、direction-ambiguity 均退出 0；复用缓存，无额外 FFT |
| `python -B P/analyze.py --repo . --out OUT/feature` | 0；4488 原状态、16 次因果前缀检查通过 |
| `python -B P/cycle_check.py --repo . --out OUT/cycle` | 0；298 帧分解、固定偏置不变性及 4 个代数控制通过 |
| `python -B P/pair-consistency/probe.py --repo . --out OUT/pairs` | 0；320 帧局部峰诊断 |
| `python -B P/background-excess/check_delivery.py --repo . --input P/background-excess/run01 --out OUT/background-check` | 0；43 个依赖/输入及 4488 个归档状态通过，无额外 FFT |
| `python -B P/frequency-diagnostic/paired.py --input P/frequency-diagnostic/run01/frames.json --out OUT/paired` | 0；共同有效帧后处理 |
| `python -B P/input-evidence-audit/audit.py --repo . --output OUT/input-audit` | 0；16 项输入 SHA、8 份 metadata |
| `python -B docs/reviews/b-mechanism-e473824/audit.py --repo <固定副本> --run OUT --out OUT/audit.json` | 0；428 项封存、307 项旧条目未改；将新生成全帧再次送入捕获分析，事件与归档相同 |

完整本轮输出见 `evidence/`，包含新生成时间线、日志、统计和 audit.json；不是作者自测的复制。测试行的 acquisition 命令实际使用 `-p test_analysis.py`，其余目录使用 `test_*.py`。`full.log` 等为原命令输出。环境显示命令首次误写 `numpy.__version`，产生 AttributeError/退出1；更正为 `numpy.__version__` 后退出0，上述研究入口均独立退出0。快照补丁首次工具格式不匹配、未应用；改正补丁格式后才完成合并，不涉及算法修正。

## 独立结果与判断

1. **没有锁定收益。** 全 4488 帧两分支 fresh 均为0、最大 acquire 均3。原/联合可捕获输入137/267；几何拒绝472/197，范围外178/323；背景1122帧数值有效700→974，但活动门后仍0。数值有效、活动门放行、锁定输出不能混为一项。
2. **中断确实存在。** spread restart 27→102，范围外中断27→88，几何中断71→42，活动门中断3→5。最长连续 eligible 5→8仍不能满足原方向聚集要求。这些是不同数量捕获尝试上的事件计数，不是相同分母的失败率；没有 fresh/HOLD，不能称失锁率。200ms 内缩候选区440帧，数值有效202→332、新增131/损失1，不是440帧语音真值。全帧控制未按该区间预裁剪。
3. **跨机差异分开处理。** 全帧 JSON 有400个浮点叶值差异，最大 `2.842170943040401e-14`；只对 angle/score/norm/residual 使用 abs `1e-10`、rel `1e-12`，其他类型/整数/状态/输入身份严格。120495 个严格叶值相同。frames.json 字节不同；result.json、protocol.json 字节相同。未改阈值或断言来促成通过。本包无新增 WAV/整数 ROM，不借用其他包结果。
4. **归因有正确边界。** 固定 pair 集合的图闭合残差不受通道常偏置影响；298帧中102原平面失败、78图残差仍失败，非标记222帧分别70/53。未把固定偏置不变性扩张为排除重取峰、有效集合变化、混响或硬件问题。无冗余图的零残差无证明力。
5. **联合支持不证明方向正确。** 窗口截断半峰宽只是下界，不是完整 FWHM；191/320 偏置选样不代表4488全帧。联合网格强制闭合是构造性质，仍检查平面残差/范数、无效 pair 回退与非正峰拒绝。异向高分解及全时序0 fresh支持“不采用”，不是精确声学性能结论。
6. **旧失败保留且身份明确。** phase-confidence 的旧 run01/portable01 未当有效最终证据；修复后按 `pair_reasons == VALID` 取拟合输入，不以非 None tau 放行 TAU_BOUND。本次检查源码及4个相位控制，引用 portable02 谱结果，未再跑该1442帧谱研究。frequency 的 NumPy int64 JSON失败及 a-input 的长路径失败摘要/旧脚本保留；后者明确不是完整原始 stderr，不伪称已归档完整日志。

## A 输入依据答复

已检查 `a-input-response/verify.py` 的历史对象绑定以及相关 RTL/说明，沿用其一次性回复，不重派录音/C任务：

- 数字 DATA1～4→mic0～3、mic0 几何原点有材料。几何文件位于 A 包 `batches/c-adapter-first-20260913/GEOMETRY.md`，绑定 `df4b756ba49a2d161c03869a0a4a28034dad15b0`；没有独立逐麦声学映射确认，不能把编号表提升为完成声学校准。
- 共同时基、两级同步、统一 phase==9、CIC3/R64/M1、共同复位/计数和4096预热有历史设计依据：A 包 `continuous-prototype-01/delivery-01/evidence/simulation/{four_mic_top.v,pdm_cic3.v}` 及 `continuous-prototype-01/RESULTS.md`，绑定 `88805ee415f137998b59b7cb197f2eeb988d17b7`。这不是物理引脚零偏斜、外部时序完整约束或麦克风群时延实测。
- 8份主机 version-binding 绑定 `94b5fe79d87e038e895878fb31030cded469bb33`，不能当 FPGA 配置读回。固定延迟/相位/增益校准仍未知；CIC×32、试听增益不属于校准。
- 约1.5m、同高、0/±45度是操作者描述，不是精密真值；手机端文件/隐藏DSP等未知保留。没有新增目标存在标签或独立目标/干扰参考。

## 合入范围、限制与合后验证

允许从上述准确提交合入121个新增 `acoustic-mechanism-20260921/` 文件及父 `checkpoint-20260923/SNAPSHOT-SHA256.json` 增量。没有默认 PHAT/Tracker、阈值、录音、A/C 工程变更。入口保留在任务包，因为是离线诊断且无候选获生产准入，不迁入默认模型。本轮不是阶段总验收，不重写公共阶段状态。

唯一三方冲突是父快照：主线61个 dynamic-das 新条目与本轮121个 acoustic 条目并行追加。核实重叠键同哈希后取并集，保留主线字段及307项原条目，最终489项实际文件哈希全部通过；旧 snapshot 原件未动。最终路径重新执行 audit.py、a-input verify、3项 acquisition 测试，均退出0，证据分别在 postmerge-audit.json/postmerge-input.txt/postmerge-tests.txt。源码未改，故不重复4,488帧FFT。

未测/不批准：新独立声学验证集、正式定位精度、目标身份、锁定/音频改善、生产 profile、完整 H3、实时/RTL/AMD/实板。phase/frequency/background 的未受影响重变换引用封存证据，不能写成全部重新跑过。没有遗留必须返修项；现有声学问题仍开放。

## 发布收尾

限定合并提交 `eb3a4482d9bdf9812b20e102fdb5af0d66069813`，非快进合并，唯一快照冲突按上文处理。首次发布后共享 main、origin/main、直接远端均为此 SHA，ahead/behind=0/0。后续本报告补记可由 Git 历史追溯，不修改批准候选。

非阻断告警：`git diff --cached --check` 报 B 原 `a-input-response/verify.py:18` 文件尾多一空行；保留准确原 blob，不为格式重写冻结源码。复核证据首次入库发生 Git 换行转换，收尾核对检出；仅为 A 新 evidence 目录添加 `-text` 并重新暂存原字节，候选/历史证据不改。这是发布存储差异，不是算法数值失败。

本批 modified/staged/untracked/ignored 有用材料归入本复核目录，其他连续采集、A 接口/帧适配候选和 Skill 未完成材料继续保留，不宣称整仓干净。未处理数按最终发布检查回报；B/C 设备不代签同步。46份独立输出入库，短期复核副本仅在逐字节确认及无独有文件后清理；失败证据保留于原批准包。不是新阶段总验收，不新增阶段快照或生产入口。
