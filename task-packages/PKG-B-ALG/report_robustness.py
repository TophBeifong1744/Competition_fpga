"""Render every prespecified condition and paired-seed diagnostics, no selection."""
import json
from pathlib import Path
import numpy as np
from audit_capture_research import ROOT,read,records,sha


def render():
    path=ROOT/'evidence/robustness-run-01';cs=read(path/'comparisons.json');pool=read(path/'pooled.json')
    ix={(r['condition'],r['method']):r for r in pool};paired=records(path/'paired.csv');lat=records(path/'latencies.csv')
    def pct(x):return f'{100*x:.2f}%'
    def val(x):return '无有效输出' if x is None else f'{x:.2f}'
    lines=['# 新噪声、方向和合成混响适用范围验证','',
        '固定 β=0.75 与 5/12 捕获，对照原 PHAT 与相同捕获规则。原默认实现和历史批次未修改。此次不调参、不选新版本。',
        '', '48 个预先声明条件 × 3 个未用种子（2026091200–1202）=144 次配对试验；67,248 个声学帧、268,992 条方法记录。',
        '', '## 结论', '',
        '同频带独立噪声的 9 个范围内条件均改善，但长尾声条件下绝对正确输出率仍低。粉红噪声和脉冲噪声多数改善。单频噪声的 9 个范围内条件均退步，4 个下降超过预设 2 个百分点，不能全面替代原 PHAT。',
        '本轮未观察到跟踪层的目标真正缺席误输出或范围外声源导致的范围内新鲜输出；这是有限样本观察，不证明概率为零，也不解决先前同锥竞争声源身份错误。',
        '副作用还包括：原始候选缺席误输出8→16/20,244帧（经5/12后两者均0）；真正缺席时HOLD旧显示2,110→2,168帧；同频带噪声+仰角边缘+长尾声的一个共同成功事件，首次正确输出变慢736ms。9项同频带条件的汇总收益不代表每个种子都改善，长尾声正前方有单种子正确率下降8.48个百分点。',
        '', '## 指标和条件', '',
        '正确率=误差≤10°的新鲜输出帧/全部稳定有目标帧；拒绝输出仍进入分母。P95仅以新鲜有效输出计，不能脱离覆盖率解读。HOLD属于旧显示，不计新鲜正确输出。',
        'front=(方位0°,仰角10°)，az_edge=(28°,0°)，el_edge=(0°,28°)，outside=(45°,0°)。允许锥半角30°，outside期望跟踪层拒绝。',
        'dry=球面直达传播；early=直达+六个一次墙面镜像反射（墙增益0.55）；early_late=再加每麦独立衰减随机FIR尾声（L2=直达幅度的0.5）。房间5×4×3m，阵列中心(2,2,1.5)m，声源距离1.5m。尾声40ms开始、350ms截断，指数包络名义60dB衰减时间250ms，不是实测或校准RT60。',
        'band=同频带独立噪声；pink=粉红噪声；tonal=1kHz随机通道相位正弦+0.05白噪声；impulsive=概率0.002的高斯脉冲+0.005白噪声。各通道按整段全频RMS归一到1，参考未门控单位探测声，不能称不同噪声具有相同带内SNR。反射后的目标能量也未归一。',
        '声源先门控再做因果线性卷积。存在标注按各麦RIR支撑集判定；发声停止后仍可能到达的尾声单列为过渡，不算目标缺席。两次发声为0.5–2.0s、2.8–4.5s，各20ms边沿。两抽头分数延迟渲染与历史生成器不同，绝对指标不直接跨批次比较。',
        '', '## 全部范围内条件（每项汇总3个种子）', '',
        '| 条件 | 原正确率 | 新正确率 | 差值/百分点 | 原P95/° | 新P95/° | 三种子差值范围/百分点 | 预设副作用标记 |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for c in cs:
        if not c['target_allowed']:continue
        ds=[100*float(r['correct_delta']) for r in paired if r['condition']==c['condition'] and r['layer']=='quorum']
        lines.append(f"| {c['condition']} | {pct(c['old_correct'])} | {pct(c['new_correct'])} | {100*c['correct_delta']:+.2f} | {val(c['old_p95'])} | {val(c['new_p95'])} | {min(ds):+.2f}～{max(ds):+.2f} | {c['side_effect_flags'] or '无'} |")
    lines+=['', '预设标记：正确率下降>2个百分点、缺席误输出增加>0.5个百分点、范围外在场新鲜输出增加>0.5个百分点、有效误差P95上升>2°。无标记不等于无退步。',
        '', '## 范围外与真正缺席检查', '', '| 条件 | 原范围外在场输出/帧数 | 新范围外在场输出/帧数 | 原缺席误输出/帧数 | 新缺席误输出/帧数 |','|---|---:|---:|---:|---:|']
    for c in cs:
        if c['target_allowed']:continue
        a=ix[c['condition'],'original_quorum'];b=ix[c['condition'],'gcc_beta075_quorum']
        lines.append(f"| {c['condition']} | {a['active_fresh_frames']}/{a['active_frames']} | {b['active_fresh_frames']}/{b['active_frames']} | {a['absent_fresh_false_outputs']}/{a['absent_frames']} | {b['absent_fresh_false_outputs']}/{b['absent_frames']} |")
    totals={}
    for method in ['original_raw','gcc_beta075_raw','original_quorum','gcc_beta075_quorum']:
        group=[s for s in pool if s['method']==method]
        totals[method]={k:sum(s[k] for s in group) for k in ['absent_fresh_false_outputs','absent_frames','absent_hold_display_frames','tail_after_emission_fresh','tail_after_emission_frames','tail_after_emission_hold']}
        t=totals[method]
        lines.append(f"\n{method}：真正缺席误输出 {t['absent_fresh_false_outputs']}/{t['absent_frames']}；缺席HOLD {t['absent_hold_display_frames']} 帧；停止发声后传播/尾声区新鲜输出 {t['tail_after_emission_fresh']}/{t['tail_after_emission_frames']}，HOLD {t['tail_after_emission_hold']} 帧。")
    lines+=['', '## 首次正确输出延迟与捕获失败', '',
        '每条件6次发声事件。仅稳定接收段内首次正确输出计成功；从发声起点计时，因此包含传播、填满分析窗及尾声稳定段等待。未捕获单列，禁止把失败当零延迟。差值仅在同种子、同次发声双方均成功的事件上计算；正值表示新方法更慢。此指标不是硬件计算耗时，也不是状态首次LOCKED时间。',
        '', '| 条件 | 原成功/6 | 新成功/6 | 共同成功数 | 延迟差中位数/ms | 最大变慢/ms |', '|---|---:|---:|---:|---:|---:|']
    latency=[]
    for c in cs:
        if not c['target_allowed']:continue
        g=[r for r in lat if r['condition']==c['condition']]
        a={(r['seed'],r['episode']):r for r in g if r['method']=='original_quorum'}
        b={(r['seed'],r['episode']):r for r in g if r['method']=='gcc_beta075_quorum'}
        differences=[float(b[k]['onset_to_correct_ms'])-float(a[k]['onset_to_correct_ms']) for k in a if a[k]['found']==b[k]['found']=='True']
        row=dict(condition=c['condition'],old_success=sum(r['found']=='True' for r in a.values()),new_success=sum(r['found']=='True' for r in b.values()),common=len(differences),median_delta_ms=float(np.median(differences)) if differences else None,max_delta_ms=max(differences) if differences else None)
        latency.append(row)
        lines.append(f"| {c['condition']} | {row['old_success']} | {row['new_success']} | {row['common']} | {val(row['median_delta_ms'])} | {val(row['max_delta_ms'])} |")
    lines+=['', '## 解释、限制与下一步', '',
        'β<1保留部分频谱幅度权重；它在同频带独立噪声中有利，但可能提高窄带强成分的影响。单频条件退步与这一机制相符，尚不能仅靠本次结果确认因果；如继续研究，应另立频谱集中度诊断与保护机制的开发集，再冻结方案使用新的验证集。当前不据此调β、锥角或捕获门限。',
        '边缘方向靠近硬性30°门限，估计偏差可使候选出锥。早反射和尾声普遍降低覆盖率：即便相对原方法改善，也可能离演示需求很远。边缘方向的误差与拒绝原因诊断应优先于宣布“支持混响”。',
        '3个种子仅作描述性适用范围检查，重叠帧不独立，不做显著性或实场通过推断。仅测试此房间、距离、方向、噪声谱和简化尾声；未覆盖实测RIR、运动、多声源、更多SNR和硬件时延。尤其不能推广为四麦或H2/H3验收结论。',
        '', '## 验证和交付', '',
        '167项测试通过（evidence/robustness-tests-02）；第一次测试因新增测试缺少适配器必填来源字段失败，修正测试后通过，robustness-tests-01原样保留。独立审计通过（evidence/robustness-audit.json）：全量落盘标签、角度、分母、配对差值、延迟和文件哈希，36份RIR支撑集；另重建12/144份完整混合输入验证哈希。未重新调参或替换算法。',
        '完整结果：evidence/robustness-run-01。源文件：payload/model/python/robustness_sweep.py；协议：payload/config/robustness-sweep.json；测试：payload/tb/python/test_robustness_sweep.py；独立复算：audit_robustness.py。',
        '全部成果留在PKG-B-ALG，供指定复核人拓芙（A）复核准确版本；尚未取得本轮批准、未合入总工程。']
    return '\n'.join(lines)+'\n',dict(totals=totals,latency=latency,adverse_conditions=[c['condition'] for c in cs if c['side_effect_flags']],report_source_sha256=sha(Path(__file__)))


if __name__=='__main__':
    report,data=render()
    for name,value in [('robustness-report.md',report),('robustness-diagnostics.json',json.dumps(data,indent=2)+'\n')]:
        out=ROOT/'evidence'/name
        if out.exists():raise ValueError('output exists')
        out.write_text(value,encoding='utf-8')
    print(json.dumps(data))
