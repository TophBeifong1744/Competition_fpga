# A 独立复核：中心 +X 录音音频对照

2026-09-15。结论：**通过限定复核，无阻断问题、无必须修改项。** 仅批准中心参考新录音绑定、手动对照入口、配置与离线验证证据入库；不批准音频改善/SNR、完整H3、自动分支、定点DAS、实时连续性、精密方位或实板验收。

## 固定版本及范围

- 直接远端核对：`task/member-b-center-audio-01` = `6c70cbcac0b24c993a49a0e69efc969dccde5a2a`。
- 基线：`058aa3095fd4df7392645004b164adb4eec52041`。
- 唯一作者增量：`task-packages/PKG-B-ALG/tasks/real-audio-compare-01/center-target-01/`，24个新增文件；无其他路径差异。旧1aa1f21包、读取/适配/DAS源码、旧证据与冻结录音均未改动。本次并非重新签发旧包批准。
- 独立工作树：`E:/ss-center-audio-review-0915`，准确SHA检出。A新输出位于本修订 `evidence/a-review-20260915/`，没有覆盖作者audio-run01。
- B日常目录 `F:/NUEC/develop` 不是临时工作树，绝不删除或操作。未改Vivado/Vitis工程；不向C派任务。

## 实际复现

环境：Windows 11 build26200、CPython3.12.14、NumPy2.3.5，无AMD DLL依赖。在独立仓库根运行以下六条，全部退出0：

```powershell
$py='C:/Users/Toph Beifong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
$rev="$pkg/center-target-01"
$out="$rev/evidence/a-review-20260915"
& $py -B "$rev/verify_package.py"
& $py -B "$rev/bind_inputs.py" --out "$out/input-check.json"
& $py -B -m unittest discover -s $pkg -p test_render_audio.py -v
& $py -B -m unittest discover -s $rev -p test_center.py -v
& $py -B "$rev/render_center.py" --out "$out/audio"
& $py -B "$rev/audit_audio.py" --audio "$out/audio" --out "$out/audit.json"
```

复跑须换新输出路径。原测试8/8、新入口4/4；23项包内文件、10项输入/依赖绑定及4份WAV/新试听哈希通过。已有输出拒绝测试对作者audio-run01五个文件前后哈希一致；输出修订外拒绝通过。测试结束后再次验证作者manifest且对准确提交检查原有文件差异为0。

另运行A独立脚本（不导入B渲染器或B审计代码）：

```powershell
& $py -B "$rev/a-review-20260915/audit_center_independent.py" . $out "$out/independent-comparison.json"
```

首次执行脚本位于A可写临时目录；入库脚本与实际运行源相同。执行日志和结果保存在新输出目录，状态 `A_INDEPENDENT_PASS`。原audit_audio的结果仍保留 `AUTHOR_CROSSCHECK_PASS` 字段，不把作者自检标签伪造为A签字。

## 独立逐项结论

| 检查 | 证据与结论 |
|---|---|
| 输入身份 | 10项pins逐项与基线Git blob及工作树SHA核对；CSV/metadata同时与f9768b80e5718dcf29baf48015305780f4b9b8e8原对象、原delivery SHA256清单一致 |
| 场景/坐标 | actual-record与INPUT-RECEIPT说明现场人声、中心+X约1.5m/约同高；仅操作者报告，无独立误差测量。mic0仍是坐标及单麦参考，不混用旧手机歌曲/相对mic1描述。1.5m未进入平面波模型 |
| 延迟符号 | 1920/343=5.597667638483965样点；向+X两路提前到达，正补偿使 `y_i[n]=x_i[n-d_i]`，d=[0,1920/343,1920/343,0]。符号测试及独立代数核对通过 |
| 共同裁剪 | 四路源索引交集[6,32000)，31994样本；编号17419～49412，均为mic0参考时间。原输入编号17413～49412连续，stream_error/error_flags为零 |
| 精确整数参考 | 对mic1/2，n-d=n-6+138/343，左/右样本权重205/343与138/343；结合mic0/3后以分母4×343整数运算并做最近偶数舍入。没有调用作者DAS或np.interp生成该golden |
| 增益 | 全部干净四通道输入及两路输出共同峰值0.007843017578125，选择满足峰值≤0.5且≤128的最大2次幂：32。64倍会超0.5。两路preview统一32倍，raw为1倍；零输入规则1倍测试通过 |
| PCM/饱和 | 4份WAV均PCM24/48kHz/mono、31994样本，无饱和；与有理数golden均0码差。单麦raw逐码等于原mic0裁剪，未补样、环绕或归一化 |
| 新旧比较 | 4份WAV字节与解码整数均严格一致。新旧result/input-check/audit JSON字节及离散、浮点字段均一致；未放宽作者1码/半LSB+1e-12预设门槛 |
| 主观记录 | 新preview精确哈希与listening-01一致。仅承接B提交的用户原话“都差不多，无发闷、失真、断音或爆音，可以下一步”；A未另做试听，不推断设备、固定音量或收益。background字段已明确为对原话的解释，不作为独立测量 |

作者浮点路径manual raw/preview量化误差分别约5.9430871148e-8、5.9430891097e-8；A有理数参考两者均5.9430870301e-8。此末位差源于预期值计算路径不同，远低于1e-12，并非新旧WAV码差；都小于半LSB=5.9604644775e-8。独立比较文件分别保留原作者统计与A有理数误差，不混称相同浮点字节。

## 非阻断限制与批准边界

1. 线性分数延迟的频率相关衰减保留。短约0.6665秒录音、未精测位置、无独立干净/噪声参考，不足以报告SNR提升或精密角误差。
2. 全部真实输入是单连续段；防覆盖和代数测试不证明流式跨帧、动态跟踪或板端播放。默认算法、自动分支和定点DAS未接入。
3. 原config/README/生成报告内“未生成/未试听”等为步骤快照，新试听记录另存；保留原字节，不回填旧状态。当前限定批准由本记录给出。
4. audit_audio只针对固定非零中心录音；其增益推导不是全零输入的通用审计接口。全零规则由新入口测试验证，不扩称任意输入均已验证。

批准后入口仍是本修订README及render_center.py，暂不迁入默认生产算法。后续完整H3及声学效果按独立评审办理。

## 发布及共享目录收尾

原有共享checkout含AGENTS/Skill等他任务改动，禁止切换/重置或覆盖。发布从本隔离工作树按准确范围合入、在合并后验证，再非强制推送main。共享main/origin/main/直接远端及本批遗漏检查另作实际补记，不以推送成功冒称共享目录已同步。

B短期分支仅在完整入库、无独有内容且收尾确认后才可清理；`F:/NUEC/develop`、其他任务和恢复引用均保留。审核目录及新运行证据归本修订，不修改公共阶段状态；本次非新阶段或整机验收。

### 实际发布核对（2026-09-15）

| 项目 | 实际结果 |
|---|---|
| 合并 | `787d4f02b7f22322c91e9fc353131bc0b95b81d7`，只含准确批准的6c70cbca新增修订及A记录 |
| 已发布版本 | `fc090dbb6493f92b12937d05695f065505091272`，已非强制推送；直接远端和origin/main一致，批准提交已在祖先链内 |
| 最终路径验证 | 合并后再次运行verify_package、8项原测试、4项新测试和A独立脚本，全部通过；结果见新证据目录postmerge-tests.log、postmerge-comparison.json |
| 新旧原件 | 作者manifest文件及10项依赖不变；本次只在center-target-01增量内发布。A新WAV、JSON、脚本和日志均已跟踪；本批未提交/忽略遗漏为0 |
| 共享目录 | 本地main仍57c50e6c99731cd57e7738ac91b02f985ad229b1，在上述核对点领先0/落后20；修订尚未出现在共享checkout。10项已修改与215项未跟踪文件和远端内容重叠，未覆盖或暂存 |
| 状态 | **已发布，批次收尾待处理**；不是技术复核失败，也不是共享main已同步。剩余跨任务同步由A工作执行/主流程协调原文件负责人处理 |
| 清理 | 本轮无删除。B短期分支、A审核工作树及恢复引用暂保留；F:/NUEC/develop为用户日常目录，未操作。其他任务和失败证据不动 |

本表补交后的最终main SHA以对话回报及本文件Git历史为准，不倒填上述检查发生时的准确版本及落后数量。入口仍为本修订README/render_center.py，不接入默认算法；批准范围没有扩大。
