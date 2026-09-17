# 2026-09-23 两项 Skill 可运行候选

结论：本目录形成两个彼此独立、可从新目录运行的作者候选；SKL-001 已完成
真实 XSim 正负例，SKL-002 已完成完整离线回归、receive-only 静态正负例和
fail-closed 板端保护。它们尚未经过本轮 B 独立复核，真实 PYNQ 准入为
`BLOCKED`，不得写成正式通过。

## 1. 固定版本与目录

| 对象 | 准确版本 / 路径 | 本轮处理 |
| --- | --- | --- |
| 固定 main | `5cfa02e51af44bb5c930babf732ddc864a1ab6cd` | 制作起点；不切换、不重置共享目录 |
| SKL-001 批准版 | `a7e1ea976da91ba735af5c0a79fffdc7d10c121f` | 活动目录未修改；复制到独立导出后增量制作 |
| SKL-002 批准版 | `3ac597d1d16982e0a5c5a114202ca8568dc28d8f` | 活动目录未修改；原 full-loopback 与测试保留 |
| SKL-001 导出 | `exports/fpga-module-verification/` | 小写入口、随包PCM源码、纠错索引、fresh run |
| SKL-002 导出 | `exports/pynq-overlay-dma-validation/` | 小写入口、独立S2MM-only profile、adapter设计、准入报告 |

两项导出的提交入口均为 `skill.md`，许可入口均为 `license.txt`。安装到要求
规范工具入口名的环境时，把 `skill.md` 原字节恢复为 `SKILL.md`；本轮已在
隔离副本中按该过程运行结构检查。

## 2. SKL-001 候选

增量内容：

- 随包提供 C 成员 C-RTL-003 的原始 `pcm4_signext_pack.v`，在局部合同中
  固定来源、归属、批准基线和 MIT 许可；case不再引用父仓库路径。
- 保持 `elastic_stage` 为第二个独立可复用案例；runner、RTL和TB行为没有
  相对批准版改写。
- 一页[纠错证据索引](exports/fpga-module-verification/references/correction-index.md)
  区分旧TB误PASS、fresh mutant首错和未重跑的B signed8历史案例。

fresh 隔离运行结果：

| 项目 | 结果 |
| --- | --- |
| runner 单元测试 | 7/7 PASS |
| PCM4 正常案例 | PASS，792次比较 |
| elastic 正常案例 | PASS，13800次检查 |
| data mutant | 预期FAIL；cycle 2 `one_edge_data` |
| ready mutant | 预期FAIL；cycle 2 `slot_ready` |
| two-stage mutant | 预期FAIL；cycle 2 `one_edge_valid` |
| 恢复正确DUT | PASS，13800次检查 |

三个负例均成功完成版本检查、编译和展开，实际在 simulate 阶段失败；工具
启动或编译错误没有被计作故障检出。

## 3. SKL-002 候选

原 `validate_profile.py` 的 full-loopback profile、生命周期mock和全部既有
测试原样保留。本轮新增：

- `validate_receive_profile.py`：独立校验同构建bit/HWH/manifest、精确AXI
  DMA实例/IP类型、simple S2MM-only、无MM2S/SG/DRE、32-bit AXIS、64-bit
  memory、14-bit length、TLAST、轮询、RX invalidate及完整包停机合同。
- SoundSight 8字记录只作为按哈希绑定的外部payload示例，通用核心不解释
  麦克风数量与字段。
- receive-only单元测试和8组可重放原始正负例；旧生命周期故障继续覆盖缓存
  陈旧、短输出、超时和完成但未静止时禁止读取/释放。
- [真实adapter设计](exports/pynq-overlay-dma-validation/references/real-adapter-design.md)
  只定义API与状态机；`pynq_probe.py`仍拒绝任何PYNQ导入、分配、MMIO或下载。

fresh 隔离运行结果：

| 项目 | 结果 |
| --- | --- |
| 全部离线单元测试 | 65个方法、74个subtest，0 failure/error/skip |
| receive-only合法profile | PASS（static、synthetic fixture） |
| receive profile重放 | 1个正例PASS；7个负例均按预期FAIL并命中目标issue code |
| 正常receive mock | PASS |
| cache stale / short output / timeout+abort-timeout | 均预期FAIL；未误写PASS |
| board guard | 非零退出、`BOARD_RUNNER_NOT_QUALIFIED`、没有创建板端输出 |

新增静态PASS仍不证明bit可部署、控制语义存在于RTL或物理TLAST正确；具体边界
见[receive合同](exports/pynq-overlay-dma-validation/references/receive-profile-contract.md)。

## 4. PYNQ准入结论

当前为 **BLOCKED**，逐项证据在
[准入报告](exports/pynq-overlay-dma-validation/references/pynq-admission-20260923.md)：

- 已知构建声明：Vivado 2025.2、`xc7z020clg400-2`，XSA/HWH中DMA确为
  S2MM=1、MM2S=0、SG=0、DRE=0、AXIS=32、memory=64、length=14；
- 尚无获批准的目标PYNQ镜像/板级支持、同构建可部署bit/HWH/manifest、目标机
  `pynq`/驱动版本、allocator/cache语义或Overlay解析记录；
- 因此真实Overlay、S2MM、TLAST、缓存、停止及恢复均为NOT_RUN。本轮没有上板。

Vitis standalone采集路径继续有效；不能把它或本轮mock写成PYNQ证据。

## 5. 证据、复现与失败记录

- 复现入口：[REPRODUCE.md](REPRODUCE.md)。
- 工作执行一页回执：[handoff.md](handoff.md)。
- fresh证据：`evidence/20260923-author-run/`；含实际命令、环境、退出码、输入
  快照、完整日志、首错和结果JSON。
- 文件清单：`MANIFEST.sha256.json`；覆盖候选交付全部文件，不自包含。
- 制作过程中的一次非技术失败见[失败记录](FAILED-RUNS.md)：PowerShell临时安装
  副本的通配符/大小写复制问题；没有伪装成Skill回归失败，也没有覆盖证据。

历史证据随批准版导出部分保留其原始时间和路径来源；其中出现的绝对路径是
历史运行记录，不是候选运行依赖。fresh复现目录为纯英文、无空格路径
`E:/skill_candidate_20260923_run02`。

## 6. 当前批准、候选与未验证范围

| 层级 | 状态 |
| --- | --- |
| 2026-09-14批准范围 | SKL-001限定模块/XSim；SKL-002限定static/mock，准确SHA如上 |
| 本轮候选 | 作者实现及fresh自检完成，等待工作执行固定准确待审SHA并交B增量复核 |
| 真实PYNQ | BLOCKED / NOT_RUN |
| Vivado综合、实现、时序、生产RTL/BD/XDC | 本轮未改、未跑，不在候选声明内 |
| B H3算法 | 本任务未修改；若出现新准确SHA，交工作执行优先做H3准入 |

## 7. 9月25日仍缺材料

1. 工作执行固定候选提交SHA、检查范围与远端发布；本目录不自行提交/推送。
2. B按准确SHA做增量独立复核；作者fresh run不能替代批准。
3. 最终竞赛包的隐私/路径/许可/链接审计及一次提交形态干净复现。
4. PYNQ路线若要主张真实能力，先补齐准入报告中的镜像、同构建物、版本、
   allocator/cache和Overlay解析证据，再由拓芙决定是否上板；否则保持BLOCKED。
5. 9月28日陌生模块/未知故障与迁移回归属于B后续范围，不写成本轮已完成。

本轮没有修改实际 one、RTL、BD、XDC、Vitis应用、CIC、H1或算法，没有下载
板卡，也没有提交、推送、合入或自行宣布验收。
