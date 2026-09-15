# 给 A：中心 +X 新录音对照复核

请复核 Competition_fpga 分支`task/member-b-center-audio-01`，以B本次回报的准确远端SHA固定版本。基线058aa3095fd4df7392645004b164adb4eec52041。唯一新增范围为`task-packages/PKG-B-ALG/tasks/real-audio-compare-01/center-target-01/`，不是重新复核或修改旧1aa1f21包。

输入是已入main并限定接收的f9768b8中心参考录音：现场人声，操作者报告阵列中心+X约1.5m、约同高；不当精密真值。mic0仍为几何原点与单麦参考，手动方位0°、仰角0°，1.5m不进入平面波延迟模型。没有改冻结实录、原DAS/读取器/适配器、默认算法、跟踪器、旧证据或主流程状态文件。

本轮申请仅为新录音绑定、手动对照入口、配置及离线验证证据入库。下一步集成位置仍为本任务包内离线入口，未申请迁入默认算法。完整H3、音频收益、自动分支、定点DAS、实时连续性及实板均不在批准范围。

请先读README.md。仓库根用CPython3.12、NumPy（作者2.3.5）运行，无AMD DLL依赖。输出路径必须不存在，以下假定首次复核：

```powershell
$pkg='task-packages/PKG-B-ALG/tasks/real-audio-compare-01'
$rev="$pkg/center-target-01"
python -B "$rev/verify_package.py"
python -B "$rev/bind_inputs.py" --out "$rev/evidence/a-input-check01.json"
python -B -m unittest discover -s $pkg -p test_render_audio.py -v
python -B -m unittest discover -s $rev -p test_center.py -v
python -B "$rev/render_center.py" --out "$rev/evidence/a-audio-run01"
python -B "$rev/audit_audio.py" --audio "$rev/evidence/a-audio-run01" --out "$rev/evidence/a-audit01.json"
```

每条检查退出码0。请独立核查正延迟符号[0,5.597667638484,5.597667638484,0]，共同裁剪[6,32000)、31994样本、参考编号17419～49412、mic0原码、所有输入/两路输出共同峰值选增益的规则及32倍试听增益、PCM24舍入/饱和、旧文件防覆盖。已有test_center的防覆盖检查针对冻结作者audio-run01，检查前后哈希不变。

作者8项原测试+4项新入口测试通过；独立实现的CSV/np.interp/PCM解码交叉自测4份WAV均0码差，无饱和。该自测仍是作者证据，不能当A独立复核。审计预设浮点路径最多1码且误差≤半LSB+1e-12，实际0码差；请分别记录复跑WAV字节、解码数值及离散结果，不能只比总数或直接调宽阈值。

用户已听本次新preview，原话“都差不多，无发闷、失真、断音或爆音，可以下一步”，见listening-01.json和精确WAV哈希。未提供设备/固定音量确认，不推断；没有取得明确改善或SNR证据。短录音、未精测位置及线性插值衰减仍限制结论，旧手机歌曲反馈没有搬到本次。

复核通过后由你按准确范围合入并在最终路径验证，B不自审自合。回报审核SHA、测试环境/结果、差异和批准边界。工作目录是用户日常`F:/NUEC/develop`，绝不可当临时worktree删除；本轮没有新增工作树。只有完整批准入库、无独有内容后，才可清理该短期任务分支；不删用户资料、恢复引用或其他任务。
