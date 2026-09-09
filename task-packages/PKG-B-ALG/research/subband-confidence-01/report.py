"""Render full-condition coverage, false-output and unknown-evidence tradeoffs."""
import numpy as np
import run_study as s
from audit import records

def render():
    p=s.s.read(s.HERE/'protocol.json');pool=s.s.read(s.HERE/'evidence/pooled.json');a=s.s.read(s.HERE/'audit.json')
    ix={(r['condition'],r['method']):r for r in pool};per=records(s.HERE/'evidence/per-seed.csv');lat=records(s.HERE/'evidence/latencies.csv')
    methods=p['methods'];totals={}
    for m in methods:
        g=[r for r in pool if r['method']==m];inside=[r for r in g if r['allowed']];outside=[r for r in g if not r['allowed']]
        totals[m]=dict(inside_active=sum(r['active_frames'] for r in inside),inside_correct=sum(round(r['active_correct_within10_rate']*r['active_frames']) for r in inside),
            outside_active=sum(r['active_frames'] for r in outside),outside_fresh=sum(r['active_fresh_frames'] for r in outside),
            absent_frames=sum(r['absent_frames'] for r in g),absent_fresh=sum(r['absent_fresh_false_outputs'] for r in g),absent_hold=sum(r['absent_hold_display_frames'] for r in g))
    lines=['# 子频带时延一致性与边界候选可信度研究','',
        '**结论：这些指标可帮助解释失败，但本轮固定筛选不能接入正式候选决策。** 范围外误输出127→0帧的代价，是范围内正确率51.54%→0.32%、捕获158/192→8/192。仅一致性筛选的正确率也只有0.35%，所以主要瓶颈先发生在子频带证据可用性与一致性，不能归咎于最后的边界包络。',
        '原全频候选已经估计在锥内时，真实范围内有12121帧被标为证据不足，而支持范围内的只有651帧；真实范围外仍有5帧被标为支持范围内。后者最终未形成跟踪输出，不代表子频带一致性已经能保证方向可信。', '',
        '本轮固定三个不重叠子频带，研究它们能否为全频候选提供独立方向证据。对照为前轮cap150+5/12（它尚未通过准入，只作为研究对象）；另加一致性筛选和方向范围筛选。原默认PHAT未修改。没有参数选择或事后调参。',
        '', '## 总体代价与收益', '',
        '下表以全部稳定有目标帧计分，保留拒绝/等待帧。范围内含恰好30°的边界，范围外为方位或仰角32°。这些分母来自本试验的固定方向分布，不是实际部署概率。',
        '', '| 方法 | 范围内正确/帧数 | 范围内正确率/% | 范围外误输出/帧数 | 范围外误输出率/% | 真正缺席误输出/帧数 | 缺席HOLD帧 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for m,t in totals.items():lines.append(f"| {m} | {t['inside_correct']}/{t['inside_active']} | {100*t['inside_correct']/t['inside_active']:.2f} | {t['outside_fresh']}/{t['outside_active']} | {100*t['outside_fresh']/t['outside_active']:.2f} | {t['absent_fresh']}/{t['absent_frames']} | {t['absent_hold']} |")
    lines+=['', '## 为什么这些量不能称为置信概率', '',
        '每个子频带用PHAT估计15麦对时延，沿用原麦对和LS有效性条件。只对有效子频带计算共同有限麦对的时延跨度中位数；用子频带与全频方向的最大两两夹角衡量方向冲突。少于2个有效子频带或共同麦对少于5对，标为unsupported（证据不足）。',
        '一致性要求方向最大夹角≤5°、时延跨度中位数≤0.5样点；边界证据还要求所有有效子频带方向及全频方向的锥角都≤30°。这只是经验包络，没有覆盖概率保证；共同反射或共同系统偏差也可能让多个频带一致地错。',
        '子频带为[300,1500)、[1500,2700)、[2700,4000]Hz。每带使用原完整频带2%峰值掩码的交集，仍要求每麦对至少12个频点。强单频可能让其他频带低于原掩码，合法窄带目标也可能只在一个频带有信息。此时未知不能被解释为声源在范围外。',
        '', '## 全部条件的输出与证据类型', '',
        '范围内行显示正确率；范围外行显示不期望的新鲜输出率。unsupported/inconsistent/边界不确定占全部稳定有目标帧比例，与full_rejected、inside_supported共同构成互斥分类。未通过的原全频候选不重复算证据不足。',
        '', '| 条件 | 范围 | 基线率/% | 一致性率/% | 包络率/% | 原候选拒绝/% | 证据不足/% | 冲突/% | 边界不确定/% |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in sorted({r['condition'] for r in pool}):
        rs=[ix[c,m] for m in methods];base=rs[0];metric='active_correct_within10_rate' if base['allowed'] else 'active_fresh_rate'
        vals=[100*r[metric] for r in rs];counts=[100*base[k]/base['active_frames'] for k in ['full_rejected','unsupported','inconsistent','boundary_uncertain']]
        lines.append(f"| {c} | {'内' if base['allowed'] else '外'} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[2]:.2f} | {counts[0]:.2f} | {counts[1]:.2f} | {counts[2]:.2f} | {counts[3]:.2f} |")
    lines+=['', '## 原候选已落入允许范围时的判别', '',
        '仅取原全频候选有效且估计在锥内的稳定有目标帧。下表检验分类与真实内/外方向的关系；样本分布与相关帧影响明显，不能将列比例直接当作校准可信度。',
        '', '| 诊断分类 | 真实范围内候选 | 真实范围外候选 |', '|---|---:|---:|']
    for k,v in sorted(a['category_risk_among_full_incone'].items()):lines.append(f"| {k} | {v.get('inside',0)} | {v.get('outside',0)} |")
    lines+=['', '## 种子差异与捕获', '',
        '| 条件（范围内） | 包络−基线正确率三种子范围/百分点 | 基线捕获/6 | 包络捕获/6 | 共同成功数 | 延迟差中位/ms |',
        '|---|---:|---:|---:|---:|---:|']
    event_totals={m:[0,0] for m in methods};deltas=[]
    for c in sorted({r['condition'] for r in pool if r['allowed']}):
        dif=[]
        for seed in p['seeds']:
            g={r['method']:r for r in per if r['condition']==c and int(r['seed'])==seed}
            dif.append(100*(float(g[methods[2]]['active_correct_within10_rate'])-float(g[methods[0]]['active_correct_within10_rate'])))
        groups={m:{(r['seed'],r['episode']):r for r in lat if r['condition']==c and r['method']==m} for m in methods}
        for m,g in groups.items():event_totals[m][0]+=sum(r['found']=='True' for r in g.values());event_totals[m][1]+=len(g)
        old,new=groups[methods[0]],groups[methods[2]]
        delta=[float(new[k]['latency_ms'])-float(v['latency_ms']) for k,v in old.items() if v['found']==new[k]['found']=='True'];deltas.extend(delta)
        med=f'{float(np.median(delta)):.2f}' if delta else '无共同成功'
        lines.append(f"| {c} | {min(dif):+.2f}～{max(dif):+.2f} | {sum(v['found']=='True' for v in old.values())} | {sum(v['found']=='True' for v in new.values())} | {len(delta)} | {med} |")
    lines+=['', '未捕获不能记零延迟；首次正确延迟从发声起点至稳定接收段内第一次≤10°新鲜输出，含传播和填窗，不是处理耗时。子频带分析新增3组相关/几何估计，未测实时计算预算。',
        '', '## 试验和交付边界', '',
        '144次配对试验：4输入类型×6方向×2传播条件×3新种子2026091500–1502。tone900/tone2200为每麦随机相位单频+白噪声，band为独立带限噪声，narrow_target为合法800–1400Hz目标+0.1RMS带限噪声；其他背景全频RMS1，不保证带内SNR相等。dry为直达，early_late为原简化早反射+随机尾声，非实测RT60。',
        '每帧先定位、诊断、更新全部会话，最后才加真值标注。所有过渡、缺席、拒绝帧仍经过会话，不拼接有目标帧。67,248份完整子频带诊断保存在features.jsonl.gz，201,744条方法结果保存frames.csv；保存输入哈希而非全部波形。gzip头可能含时间信息，复现应比解压内容/数值，不假装跨次压缩字节一致。',
        '173项测试通过，audit.json独立从落盘子频带方向和时延重算指标/分类，核对原候选筛选语义、接收标签、角度、分母、延迟及哈希，并重建8份输入。原552个文件保持不变。新指标均为诊断量，未经概率校准；3个种子为描述性结果，不作显著性或实板结论。',
        '成果集中于research/subband-confidence-01，默认算法未修改。本轮待指定复核人拓芙（A）确认，未提交、推送或合入总工程。']
    loss=s.s.read(s.HERE/'loss-diagnosis.json')
    lines+=['', '## 为什么证据大量不足：事后描述性检查', '',
        '以下检查在看到主试验失败后进行，没有修改频带、门限或主试验结果，不作为独立验证。每个输入类型含9234个稳定有目标帧（包含内/外方向）。',
        '', '| 输入 | 0个有效子带 | 1个有效子带 | 2个有效子带 | 3个有效子带 |', '|---|---:|---:|---:|---:|']
    for noise,c in loss['counts'].items():lines.append(f"| {noise} | {c.get('valid_bands_0',0)} | {c.get('valid_bands_1',0)} | {c.get('valid_bands_2',0)} | {c.get('valid_bands_3',0)} |")
    lines+=['', '合法800–1400Hz目标完全落在第一子带，第二、第三子带在9234帧中均没有有效解，要求至少两个子带一致必然阻断这类目标。同频带独立噪声也仅82/9234帧得到两个有效子带，其低子带大量触发原残差拒绝；频点数量足够不等于相位与时延可靠。单频条件则同时出现其他频带被全频峰值掩码压掉、干扰所在子带残差过大的问题。拒绝原因可重叠，明细见loss-diagnosis.json。',
        '另外加入12次无背景噪声对照，复用主试验第一个种子，仅检查实现和传播效应：6个直达方向每个289帧均有3个有效子带，说明实现不是在所有条件下都失效。加入早反射与尾声后，可用子带减少、方向冲突增多，说明混响本身也破坏跨子带一致。',
        '无噪声、直达、真实恰好30°的289帧全部被标为边界不确定。所有子带估计都严格落入范围的要求，对边界缺少误差余量；分数时延插值或近场到平面几何等微小偏差都可能影响结果。该现象尚未证明是哪一种误差单独造成，需要专门校准。',
        '', '## 下一步建议', '',
        '不要继续把“至少两个窄子带有效”作为全场景硬性前提，也不要把unsupported当作已知范围外。优先研究保留宽频跨度的留一频段扰动检查，并单独记录证据可用性；在全频候选基础上评估删去某段后是否显著改变时延，可减少固定切成窄子带造成的信息损失。此方向尚未在本轮实现或验收。',
        '边界可信度需分别校准方向偏差和估计波动，再定义未知状态如何交给上层处理；经验方向包络不能包装成置信概率。当前继续保留默认算法和30°规则，这批结果固定为失败参照，新方案应另设开发/验证集。']
    return '\n'.join(lines)+'\n',dict(totals=totals,event_totals=event_totals,common_latency_pairs=len(deltas),median_latency_delta=float(np.median(deltas)) if deltas else None,max_latency_delta=max(deltas) if deltas else None)

if __name__=='__main__':
    text,data=render()
    for name in ['REPORT.md','diagnostics.json']:
        path=s.HERE/name
        if path.exists():raise ValueError('output exists')
        if name.endswith('.md'):path.write_text(text,encoding='utf-8')
        else:s.s.entry.write_json(path,data)
    print(data)
