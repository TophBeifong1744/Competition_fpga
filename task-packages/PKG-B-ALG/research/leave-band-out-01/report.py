import numpy as np
import csv
import run_study as s

def records(path):
    with path.open(encoding='utf-8',newline='') as file:return list(csv.DictReader(file))

def render():
    p=s.s.read(s.HERE/'protocol.json');pool=s.s.read(s.HERE/'evidence/pooled.json');a=s.s.read(s.HERE/'audit.json')
    ix={(r['condition'],r['method']):r for r in pool};methods=p['methods'];per=records(s.HERE/'evidence/per-seed.csv');lat=records(s.HERE/'evidence/latencies.csv')
    totals={};events={};overview=[]
    for m in methods:
        g=[r for r in pool if r['method']==m];inside=[r for r in g if r['allowed']];outside=[r for r in g if not r['allowed']]
        totals[m]=dict(inside_frames=sum(r['active_frames'] for r in inside),correct=sum(round(r['active_correct_within10_rate']*r['active_frames']) for r in inside),
            outside_frames=sum(r['active_frames'] for r in outside),outside_fresh=sum(r['active_fresh_frames'] for r in outside),
            absent_frames=sum(r['absent_frames'] for r in g),absent_fresh=sum(r['absent_fresh_false_outputs'] for r in g),absent_hold=sum(r['absent_hold_display_frames'] for r in g))
        g=[r for r in lat if r['allowed']=='True' and r['method']==m];events[m]=dict(success=sum(r['found']=='True' for r in g),events=len(g))
    lines=['# 保留宽频信息的留一频段扰动检查','',
        '**结论：留一频段比窄子带独立定位更能保留输出，但当前规则仍不能成为已验收的候选保护或置信判据。** 在同一批输入上，窄子带筛选仅有568个正确输出，留一严格检查有9544个，未知保留方案有10609个，对照为11781个。未知保留的正确输出数量约为对照90.1%，范围外误输出119→57（减少52.1%），捕获147/192→144/192。',
        '代价仍须保留：同频带噪声正确率20.34%→14.78%，范围外仍有57个新鲜误输出；共同成功事件中最大首次正确输出延迟增加1002.67ms。合法窄带目标正确率45.24%保持不变，但下面的证据可用性检查表明，这不能解释为可信度已得到独立验证。', '',
        '本轮研究的是候选对频段删除是否敏感，不将删频估计直接替换为输出。全频对照为前轮未准入的cap150+5/12，不是已替换默认算法。所有方向范围、时延/LS验收、捕获规则保持不变。',
        '', '## 总体表现', '',
        '正确率以全部稳定范围内帧作分母；范围内含恰好30°，范围外为方位/仰角32°。不把低覆盖率带来的零误输出称为保护成功。',
        '', '| 方法 | 范围内正确/帧数 | 正确率/% | 范围外误输出/帧数 | 误输出率/% | 捕获成功/事件 | 真正缺席误输出 | 缺席HOLD帧 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m,t in totals.items():lines.append(f"| {m} | {t['correct']}/{t['inside_frames']} | {100*t['correct']/t['inside_frames']:.2f} | {t['outside_fresh']}/{t['outside_frames']} | {100*t['outside_fresh']/t['outside_frames']:.2f} | {events[m]['success']}/{events[m]['events']} | {t['absent_fresh']}/{t['absent_frames']} | {t['absent_hold']} |")
    lines+=['', '## 四组配对方法', '',
        '- cap150_quorum：不增加检查的全频对照。',
        '- split_strict_quorum：上一轮固定窄子带一致性筛选，在本轮相同新输入上重跑，便于直接比较。不是从上一批绝对数值推断进步。',
        '- loo_strict_quorum：至少2次删频估计有效且与全频共享至少5对时延；最大方向变化≤5°且每次时延绝对变化中位数的最大值≤0.5样点才保留。',
        '- loo_known_only_quorum：规则相同，但不足2次可比删除时标unknown并保留原流程，仅拒绝有足够证据的sensitive候选。unknown通过不是置信认可。',
        '', '每次删除[300,1500)、[1500,2700)、[2700,4000]Hz中的一段，保留另外两段。全频2%峰值掩码及cap150权重预先计算后固定，不重新定掩码或限幅。这样隔离“删频”影响，但也不能恢复已被原掩码压掉的信息。',
        '比较的是全频与各次删除估计的变化，不要求3个窄子带各自定位。stable仅表示至少2次可比较删除均在门限内，第三次可能不可用，不是“全部证据一致”或校准可信度。全频本来无效的帧在所有筛选中仍无效。',
        '', '## 按输入类型统计（范围内）', '',
        '| 类型 | 全频正确率/% | 窄子带筛选/% | 留一严格/% | 留一仅拒敏感/% |', '|---|---:|---:|---:|---:|']
    for noise in p['noises']:
        row=dict(noise=noise)
        for m in methods:
            g=[r for r in pool if r['allowed'] and r['method']==m and r['condition'].startswith(noise+'__')]
            row[m]=sum(round(r['active_correct_within10_rate']*r['active_frames']) for r in g)/sum(r['active_frames'] for r in g)
        overview.append(row);lines.append('| '+noise+' | '+' | '.join(f'{100*row[m]:.2f}' for m in methods)+' |')
    lines+=['', '## 全部条件与未知比例', '',
        '范围内行显示正确输出率，范围外行显示不期望的新鲜输出率。unknown、sensitive、stable与full_rejected互斥，以下类别比例以全部稳定有目标帧作分母。',
        '', '| 条件 | 内/外 | 全频/% | 窄子带/% | 留一严格/% | 留一仅拒敏感/% | 未知/% | 敏感/% | 稳定/% |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in sorted({r['condition'] for r in pool}):
        rs=[ix[c,m] for m in methods];base=rs[0];key='active_correct_within10_rate' if base['allowed'] else 'active_fresh_rate'
        vals=[100*r[key] for r in rs];cats=[100*base[k]/base['active_frames'] for k in ['unknown','sensitive','stable']]
        lines.append('| '+c+' | '+('内' if base['allowed'] else '外')+' | '+' | '.join(f'{v:.2f}' for v in vals+cats)+' |')
    lines+=['', '## 诊断量与真实方向的关系', '',
        '只取全频候选有效且估计在30°范围内的稳定有目标帧，检查分类与真内/外是否相关。样本类别比例受本试验方向分布影响，不能换算成部署置信概率。',
        '', '| 分类 | 真范围内 | 真范围外 |', '|---|---:|---:|']
    for k,v in sorted(a['category_risk_among_full_incone'].items()):lines.append(f"| {k} | {v.get('inside',0)} | {v.get('outside',0)} |")
    lines+=['', '某次删频估计跨越30°边界是另一个诊断标记，本轮不据此扩大范围或改写输出。小于5°的方向扰动也可能跨过边界；stable与始终在范围内不是一回事。',
        '', '| 分类/是否跨界 | 真范围内 | 真范围外 |', '|---|---:|---:|']
    for k,v in sorted(a['crossing_risk_among_full_incone'].items()):lines.append(f"| {k} | {v.get('inside',0)} | {v.get('outside',0)} |")
    lines+=['', '## 逐种子变化与延迟', '',
        '以下比较留一仅拒敏感方案与全频对照。延迟仅对同条件/种子/发声事件双方均成功者作差，失败单列；发声起点至稳定接收段首个正确输出包含传播和填窗，不是处理耗时。',
        '', '| 范围内条件 | 正确率差三种子范围/百分点 | 对照捕获/6 | 新捕获/6 | 共同成功 | 延迟差中位数/ms |', '|---|---:|---:|---:|---:|---:|']
    changes=[]
    for c in sorted({r['condition'] for r in pool if r['allowed']}):
        ds=[]
        for seed in p['seeds']:
            g={r['method']:r for r in per if r['condition']==c and int(r['seed'])==seed}
            ds.append(100*(float(g[methods[-1]]['active_correct_within10_rate'])-float(g[methods[0]]['active_correct_within10_rate'])))
        old={(r['seed'],r['episode']):r for r in lat if r['condition']==c and r['method']==methods[0]};new={(r['seed'],r['episode']):r for r in lat if r['condition']==c and r['method']==methods[-1]}
        delta=[float(new[k]['latency_ms'])-float(v['latency_ms']) for k,v in old.items() if v['found']==new[k]['found']=='True'];changes.extend(delta)
        median=f'{np.median(delta):.2f}' if delta else '无共同成功'
        lines.append(f"| {c} | {min(ds):+.2f}～{max(ds):+.2f} | {sum(v['found']=='True' for v in old.values())} | {sum(v['found']=='True' for v in new.values())} | {len(delta)} | {median} |")
    availability=s.s.read(s.HERE/'availability.json')
    lines+=['', '## 稳定不等于提供了独立证据', '',
        '事后描述性检查（不改规则、不作新验证）：检查可比较的删除是否真正移除了原掩码保留的频点。每个保留频点恰好出现在两个补集，因而可由三个补集计数重建全频计数；这一关系已由单元测试核对。',
        '', '| 类型 | 稳定帧 | 仅2次可比较 | 3次可比较 | 所有可比删除均未移除任何保留频点的帧 |', '|---|---:|---:|---:|---:|']
    for noise,c in availability['counts'].items():lines.append(f"| {noise} | {c['stable_frames']} | {c.get('comparable_2',0)} | {c.get('comparable_3',0)} | {c['frames_all_comparisons_remove_zero_bins']} |")
    lines+=['', '合法窄带目标5622个稳定帧全部只有2次可比较删除，且这两次均未移除任何原保留频点：删的是原本就没有有效信息的频段。目标不再被误伤是实际改善，但这种稳定是同一有效频谱被重复比较，不能算两份独立支持。第三次删去目标频带后无法比较，当前规则允许忽略它。',
        '在全频候选已经估计在锥内的帧中，仍有540个真范围外候选被标为stable，其中337个甚至没有任何可比较删频方向跨界。因此“小扰动”或“不跨界”仍可能围绕一个错误方向稳定，不能直接转化为边界可信度。',
        '', '## 下一步建议', '',
        '若继续推进，应先定义扰动是否有效：被移除频段是否包含足够的实际保留信息，以及删频失败本身意味着什么。将未知、无有效变化、敏感分开记录，避免把未产生变化的重复频谱当作独立佐证。此处只是后续设计方向，未在当前批次追加调参。',
        '边界风险还需结合几何残差、模型偏差及时间稳定性单独验证，不能只增加一个删频稳定阈值。保留本批为固定参照，另设新开发/验证集；当前默认算法及方向范围不变。',
        '', '## 复现和限制', '',
        '144次配对试验、3个全新种子2026091600–1602，输入为1.2/2.5kHz单频干扰、同频带独立噪声、合法800–1400Hz窄带目标；方向front(0°,10°)、az28/30/32、el28/32，传播为直达或原简化早反射+尾声。与历史种子隔离，固定规则不拟合、不选优，阈值尚未校准。',
        '背景全频RMS1，合法窄带目标控制背景RMS0.1；不同类型不是相同带内SNR。每输入5s、467帧，全部帧连续更新跟踪，最后才加接收存在和方向标签；尾声属于过渡，不误当真正缺席。',
        '67,248份原/删除候选详细诊断保存在features.jsonl.gz，268,992条方法行及逐种子/汇总/延迟结果保存evidence。压缩头可能含时间，跨次复现比较解压内容和数值，不要求gzip字节一致。',
        '173项测试通过；audit.json独立从落盘方向/时延重算留一诊断，核对接收标签、筛选语义、角度、统计和延迟，并重建8份输入。旧窄子带决策与保存的诊断轨迹相连，没有宣称独立重算其完整算法。原579个文件哈希未改变。',
        '输出减少造成的误输出下降不证明定位问题解决，多个删除结果共享输入、不是独立投票。三种子只作描述性分析，没有实测RIR、实板、实时预算或H2/H3结论。',
        '本轮成果集中于research/leave-band-out-01，默认算法未改，未提交、推送或合入。指定复核人为拓芙（A），当前待复核。']
    return '\n'.join(lines)+'\n',dict(totals=totals,events=events,overview=overview,latency_common_pairs=len(changes),latency_median_delta=float(np.median(changes)) if changes else None,latency_max_delta=max(changes) if changes else None)

if __name__=='__main__':
    text,data=render()
    for name in ['REPORT.md','diagnostics.json']:
        out=s.HERE/name
        if out.exists():raise ValueError('output exists')
        if name.endswith('.md'):out.write_text(text,encoding='utf-8')
        else:s.s.entry.write_json(out,data)
    print(data)
