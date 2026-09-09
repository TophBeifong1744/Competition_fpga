import csv
import numpy as np
import run_study as s

def records(path):
    with path.open(encoding='utf-8',newline='') as file:return list(csv.DictReader(file))

def render():
    p=s.s.read(s.HERE/'protocol.json');a=s.s.read(s.HERE/'audit.json');pool=s.s.read(s.HERE/'evidence/pooled.json');lat=records(s.HERE/'evidence/latencies.csv');per=records(s.HERE/'evidence/per-seed.csv')
    methods=p['methods'];ix={(r['condition'],r['method']):r for r in pool};totals={};events={}
    for m in methods:
        g=[r for r in pool if r['method']==m];inside=[r for r in g if r['allowed']];outside=[r for r in g if not r['allowed']]
        totals[m]=dict(inside_frames=sum(r['active_frames'] for r in inside),correct=sum(round(r['active_correct_within10_rate']*r['active_frames']) for r in inside),outside_frames=sum(r['active_frames'] for r in outside),outside_fresh=sum(r['active_fresh_frames'] for r in outside),absent_frames=sum(r['absent_frames'] for r in g),absent_fresh=sum(r['absent_fresh_false_outputs'] for r in g),absent_hold=sum(r['absent_hold_display_frames'] for r in g))
        g=[r for r in lat if r['method']==m and r['allowed']=='True'];events[m]=dict(success=sum(r['found']=='True' for r in g),total=len(g))
    lines=['# 扰动是否真正移除了参与定位的信息','',
        '**结论：可以识别“没有真正改变定位频谱”的伪稳定，但还不能据此证明方向可信。** 新种子试验中，5443个合法窄带目标帧原本被标stable：两次可比删除合计10886次都没有移除原保留频点，另一次删掉目标所在频带后无法定位。这5443帧现在全部改为unknown；另外41个单频干扰帧也由stable改为unknown。',
        '新旧规则的67248对跟踪输出逐帧一致，正确输出均11801帧、范围外误输出均205帧、捕获均148/192次。这一步纠正的是证据标注，尚未改善定位性能；两种规则都保留unknown，所以稳定改未知不会直接改变输出。',
        '有效扰动也不保证方向正确：在全频候选已估计在允许锥内的样本中，仍有563个真实范围外候选被新规则标stable。删除贡献足够与“删除了能辨认目标方向的信息”不是同一个命题。', '',
        '本轮先验证删除是否改变实际用于GCC的频谱贡献，再评价删后的稳定性。这里的“有效”是测量定义，不代表删掉了真实目标信息，也不能区分目标与干扰。原默认PHAT未改，cap150只是前轮未准入研究对照。',
        '', '## 判定规则', '',
        '对每个麦对，重建全频cap150实际使用的复频谱G(f)，计算删除频段的保留频点数及sum(|G_deleted|)/sum(|G_full|)。这是幅度贡献份额，不是波形能量、信噪比或信息论指标。另保存f²加权幅度份额作为相关曲率的描述性代理，未用于筛选，更不是已校准的Fisher信息。',
        '一次删除要作为有效比较，需原候选和删后候选都有效，且至少5对共同有限时延各自满足：删除≥3个原保留频点、删除幅度份额在10%～80%。门限在运行前固定，尚未校准。超过80%也许确实删除了重要成分，但在本规则中不足以给剩余结果作稳定性佐证。',
        '类别分开记录：no_change=没有删到保留频点；uncomparable=删后解失效或共同有效麦对不足；weak_or_excessive=贡献过小、过大或满足门限的麦对不足；effective=满足定义。原全频无效单列full_rejected。各删除类别按此顺序互斥，uncomparable不等于“信息没有被删除”。',
        '仅以有效删除计算原留一变化量；至少2次才判稳定/敏感，否则未知。前后规则都保留未知、仅拒绝敏感，因此本轮主要改变证据解释，不保证误输出减少。方向阈值5°、时延变化中位数0.5样点、30°范围和5/12捕获均不变。',
        '', '## 稳定性标签如何变化', '',
        '下面仅统计稳定有目标帧，包含内/外方向。原稳定被改为未知，表示先前缺乏足够有分量的扰动证据，不表示现在知道候选一定错误。',
        '', '| 输入 | 原稳定→新稳定 | 原稳定→未知 | 原敏感→未知 | 原敏感→稳定 |', '|---|---:|---:|---:|---:|']
    for noise,v in a['transitions'].items():lines.append(f"| {noise} | {v.get('stable->stable',0)} | {v.get('stable->unknown',0)} | {v.get('sensitive->unknown',0)} | {v.get('sensitive->stable',0)} |")
    lines+=['', '## 单次扰动的类别', '',
        '以全频有效的稳定有目标帧为对象，每帧3次删除。',
        '', '| 输入 | 没有变化 | 删后不可比 | 太弱/过量或麦对不足 | 有效比较 |', '|---|---:|---:|---:|---:|']
    for noise,v in a['impact_status_counts'].items():lines.append(f"| {noise} | {v.get('no_change',0)} | {v.get('uncomparable',0)} | {v.get('weak_or_excessive',0)} | {v.get('effective',0)} |")
    lines+=['', '## 对实际跟踪的影响', '',
        '正确率包含所有稳定范围内帧，含恰好30°边界；范围外为方位/仰角32°。原留一与新规则在相同输入配对，不从历史批次绝对数值推断改善。',
        '', '| 方法 | 范围内正确/帧数 | 正确率/% | 范围外误输出/帧数 | 捕获成功/事件 | 真正缺席误输出 | 缺席HOLD |', '|---|---:|---:|---:|---:|---:|---:|']
    for m,t in totals.items():lines.append(f"| {m} | {t['correct']}/{t['inside_frames']} | {100*t['correct']/t['inside_frames']:.2f} | {t['outside_fresh']}/{t['outside_frames']} | {events[m]['success']}/{events[m]['total']} | {t['absent_fresh']}/{t['absent_frames']} | {t['absent_hold']} |")
    lines+=['', '## 全部条件', '',
        '范围内为正确输出率，范围外为错误产生新鲜输出的比例。分类百分比按全部稳定有目标帧计算。',
        '', '| 条件 | 内/外 | 全频/% | 原留一/% | 有效扰动留一/% | 新未知/% | 新稳定/% |', '|---|---|---:|---:|---:|---:|---:|']
    for c in sorted({r['condition'] for r in pool}):
        rs=[ix[c,m] for m in methods];base=rs[0];metric='active_correct_within10_rate' if base['allowed'] else 'active_fresh_rate'
        vals=[100*r[metric] for r in rs]+[100*base[k]/base['active_frames'] for k in ['unknown','stable']]
        lines.append('| '+c+' | '+('内' if base['allowed'] else '外')+' | '+' | '.join(f'{v:.2f}' for v in vals)+' |')
    lines+=['', '## 真实内外方向与新标签', '',
        '只取全频候选有效且估计已在30°范围内的稳定有目标帧；频数依赖本试验方向/噪声分布，不是部署置信概率。',
        '', '| 新类别 | 真范围内 | 真范围外 |', '|---|---:|---:|']
    for k,v in sorted(a['category_risk_among_full_incone'].items()):lines.append(f"| {k} | {v.get('inside',0)} | {v.get('outside',0)} |")
    lines+=['', '## 新规则相对原留一：种子与延迟', '',
        '| 范围内条件 | 正确率差三种子范围/百分点 | 原捕获/6 | 新捕获/6 | 共同成功 | 延迟差中位/ms |', '|---|---:|---:|---:|---:|---:|']
    differences=[]
    for c in sorted({r['condition'] for r in pool if r['allowed']}):
        ds=[]
        for seed in p['seeds']:
            g={r['method']:r for r in per if r['condition']==c and int(r['seed'])==seed}
            ds.append(100*(float(g[methods[2]]['active_correct_within10_rate'])-float(g[methods[1]]['active_correct_within10_rate'])))
        old={(r['seed'],r['episode']):r for r in lat if r['condition']==c and r['method']==methods[1]};new={(r['seed'],r['episode']):r for r in lat if r['condition']==c and r['method']==methods[2]}
        delta=[float(new[k]['latency_ms'])-float(v['latency_ms']) for k,v in old.items() if v['found']==new[k]['found']=='True'];differences.extend(delta)
        median=f'{np.median(delta):.2f}' if delta else '无共同成功'
        lines.append(f"| {c} | {min(ds):+.2f}～{max(ds):+.2f} | {sum(v['found']=='True' for v in old.values())} | {sum(v['found']=='True' for v in new.values())} | {len(delta)} | {median} |")
    lines+=['', '延迟仅对双方同条件/种子/事件均成功时比较，未捕获单列，不记零；从发声起点至稳定接收段首个正确输出，含传播和分帧，不是计算耗时。',
        '', '## 边界、证据和交付', '',
        '144次配对试验，3个新种子2026091700–1702；2种单频干扰、同频带噪声、合法800–1400Hz窄带目标，6方向及直达/简化混响两条件。背景全频RMS不意味着相同带内SNR；原生成器和LS模型局限保持。未拟合/选优或事后调参。',
        '每次5s、467帧，先定位、测扰动、更新跟踪，最后加接收存在和方向真值。拒绝/缺席/过渡帧都更新会话，尾声不错误算作真正缺席。所有方法共享原/删频候选。',
        '173项测试通过；audit.json独立重算删除贡献资格、旧新标签、接收标注、角度、计数及延迟；重建8份完整输入并独立核算40帧的频谱删除份额。67,248份诊断和201,744条方法输出保存于evidence，原606个文件哈希不变。',
        '这些指标只是频谱扰动的可用性说明；真正目标信息、空间可辨识性、噪声贡献和系统偏差仍未分离。三个种子仅作描述性检查，不是实板或H2/H3结论。',
        'compare_outputs.py另外核对全部67248对新旧跟踪行的新鲜输出、状态、原因、HOLD、角度、坐标、候选有效性和显示有效期，差异为0；详见output-equivalence.json。诊断标签变化不伪装成性能提升。',
        '后续可保留“扰动是否有效”作为诊断字段，另行研究有效扰动仍支持的错误范围内候选。当前不应靠把所有unknown拒绝来制造低误输出，也不因stable标签宣称高置信度。本批固定保留，不在结果后重调10%～80%门限。',
        '成果在research/effective-perturbation-01，默认算法未改，未提交、推送或合入。指定复核人拓芙（A），本轮待复核。']
    return '\n'.join(lines)+'\n',dict(totals=totals,events=events,common_latency_pairs=len(differences),median_latency_delta=float(np.median(differences)) if differences else None,max_latency_delta=max(differences) if differences else None)

if __name__=='__main__':
    text,data=render()
    for name in ['REPORT.md','diagnostics.json']:
        out=s.HERE/name
        if out.exists():raise ValueError('output exists')
        if name.endswith('.md'):out.write_text(text,encoding='utf-8')
        else:s.s.entry.write_json(out,data)
    print(data)
