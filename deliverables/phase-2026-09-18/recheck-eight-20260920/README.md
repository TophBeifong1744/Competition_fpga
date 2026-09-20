# 9/18阶段再次复验：八段开发输入接收后

实际日期2026-09-20；固定主线 `78e8eae1ee6a5a085752ced7e8c90f92e0be3981`。

结论：**声学基线与完整H3仍未通过；八段开发/诊断材料接收完成。** 不倒填9/18快照，不撤销已有限定批准，不把9/23正式M1或外设效果临时追加到9/18判据。

## 原判据逐项裁决

| 项目 | 证据与裁决 |
| --- | --- |
| 四路实际输入与单麦/手动/自动对照 | 既有三路离线诊断批准保持。新增94b5fe7八段获B开发/诊断限定PASS并完成A本机收尾；不再0/8或待录制。新八段不自动继承三路输出/效果批准。 |
| 目标存在与方向指标 | 未通过：两段背景1119/1122帧过现有门；六段48标记峰可复现，但区间仅候选、角度目测，尚不足以正式验收P50/P95、有效率与错向率。上述计数不是正式误报率。 |
| 音频收益 | 未通过：缺阵列处同步目标/干扰参考和可核验收益；播放源WAV不等于同步干净参考。标记、保护区、混响不得混入评分；同批调参仍属开发集。 |
| 整数golden、格式/异常、断流 | run05准确7a17edd维持B限定PASS，39测试、14数组/事件比较复用合后记录；最终生产数制及AMD全链逐级位精确仍未关闭。 |
| 集成合同、缓存与周期预算 | 未通过：28d5c77接口包已复现，仍待A/B生产合同裁决；73,900周期仅历史FFT/IFFT槽数之和，不是全链最坏周期上界。 |
| 两项Skill的9/18范围检查 | 保持a7e1ea9模块仿真、3ac597d离线限定批准，本轮核对活动目录无变化。9/23候选/迁移与真实PYNQ路线按原日历，不作最终Skill验收。 |

依据：[B八段复核](../../../docs/reviews/eight-94b5fe7/B-REVIEW.md)、[A材料收尾](../../../docs/reviews/eight-94b5fe7/A-LOCAL-CLOSEOUT.md)、[上轮复验与接口复现](../recheck-20260920/README.md)、[run05合后补充](../../../docs/reviews/h3-run05-7a17edd/POSTMERGE-SUPPLEMENT.md)。

## 当前分工与未完成项

- A：八段已交齐，不重派录制、FFT或耐久；与B裁决生产接口/数制/预算，沿已有任务推进9/23正式采集项及Skill候选。本机未提交帧适配/Skill成果不视为批准。
- B：run05、S1、计时入口、八段复核均已完成。接下来重点为存在门、候选边界敏感性、声学评价与数制/golden/周期预算；不重复已关闭复核，不把开发集改称独立验证集。
- C：旧b1d51d4限定模块批准保留；d63544d已改变接口，未见绑定新版的独立批准。继续原定转台/摄像头驱动及效果任务，不新增声学任务或交期；其外设状态不替代声学H3裁决。

下一正式检查9/23，V1总验收10/1；不自动顺延。

## 实际检查、复用与未测

本轮cwd为A共享仓库根。`git fetch origin`、`git ls-remote --heads origin main`、`git rev-list --left-right --count main...origin/main`成功，三端均为固定主线，ahead/behind=0/0。首次沙箱fetch写FETCH_HEAD被拒、远端凭据失败；授权环境重试成功，不属于技术测试失败。

实际执行`git diff --name-only <SHA> HEAD -- <路径>`四项，均退出0、无差异：

| SHA | 路径 |
| --- | --- |
| a7e1ea976da91ba735af5c0a79fffdc7d10c121f | skill/fpga-module-verification/ |
| 3ac597d1d16982e0a5c5a114202ca8568dc28d8f | skill/pynq-overlay-dma-validation/ |
| 7a17edd2b5408e10608d954f3e7fa11cb62fe34b | task-packages/PKG-B-ALG/tasks/h3-complete-20260918/ |
| 94b5fe79d87e038e895878fb31030cded469bb33 | task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918/ |

复用B八段72当前哈希、BIN/UART/CSV/32 WAV逐值、10离线测试、48标记峰；A286文件原字节检查；run05合后及上轮接口复现。批准范围未变，本次不重跑技术测试。未执行新算法、XSim、综合时序、板测或PYNQ；未代签B/C本机未推送工作。

H3-RUN05-FIRST-FAILURE-RAW-01仍NOT_ARCHIVED：第二受控副本和访问控制未验证；保留归档缺口，不撤销run05限定技术PASS，不宣称流程全部关闭。
