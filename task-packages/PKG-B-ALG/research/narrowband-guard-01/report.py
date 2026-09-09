"""Render all heldout conditions without tuning or selecting on heldout results."""
import numpy as np
import study as s
from audit import records

def render():
    selection=s.s.read(s.HERE/'development/selection.json');name=selection['selected'];dec=s.s.read(s.HERE/'validation/gates.json')[name]
    pool=s.s.read(s.HERE/'validation/pooled.json');ix={(r['condition'],r['method']):r for r in pool}
    per=records(s.HERE/'validation/per-seed.csv');lat=records(s.HERE/'validation/latencies.csv')
    def pct(v):return f'{100*v:.2f}'
    def num(v):return '无输出' if v is None else f'{v:.2f}'
    success=selection['development_passed'] and dec['passed']
    lines=['# 窄带干扰候选保护机制研究','',
        f"冻结候选：**{name}**。开发准入：{'通过' if selection['development_passed'] else '未通过，仅依预先规则选作诊断'}；全新验证集准入：{'通过' if dec['passed'] else '未通过'}。{'可供A复核的离线候选，仍不替换默认。' if success else '当前不建议替换原默认或作为已验收保护机制。'}",'',
        '本轮结论：强频点限幅有部分收益，但尚不能成为通用窄带保护。新验证集72个条件中22个触发失败门限（19个单频范围内条件、3个范围外条件）。2.8kHz的范围内平均正确率从未保护的44.68%升到63.96%，仍低于原PHAT的77.36%。宽带相对PHAT收益保留约97.3%，合法窄带目标控制未见超过2个百分点的退步。',
        '需要保留的副作用：2.8kHz、32°范围外、直达条件误输出从β的4/867增至14/867（原PHAT为0）；早反射条件从0增至9/861。宽带32°直达则沿用了β的9/867误输出，未进一步增加，但仍未达到相对PHAT的门限。真正缺席三算法均0/30366，不可用它掩盖范围外声源误捕获。宽带捕获成功事件45/54→44/54；缺席HOLD旧显示3157→3247帧，最大共同成功事件延迟增加10.67ms。', '',
        '## 方案与选择', '',
        '- fallback035：每麦对计算分析频带内最大3个互谱幅度之和/总互谱幅度，再取15麦对中位数；≥0.35时整帧使用原PHAT，否则用β=.75。无方向真值、存在标签或未来帧输入；不尝试判断声源身份。',
        '- cap150：保留β=.75的幅度权重，但将保留频点的权重限制在这些权重中位数的1.5倍；不改变原频点掩码、15麦对几何和LS拒绝标准。',
        '两方案参数均在开发试验前写入protocol.json；仅在通过全部开发门限的方案中按范围内单频正确率选优。若均不通过，按相同指标冻结一项做探索性验证，不当作开发通过。验证阶段只运行原PHAT、未保护β=.75及冻结的一项。',
        '', '| 开发候选 | 全部门限 | 单频平均正确率/% | 宽带相对PHAT平均收益/百分点 | 未通过项 |','|---|---|---:|---:|---|']
    for m,d in selection['decisions'].items():lines.append(f"| {m} | {'通过' if d['passed'] else '未通过'} | {pct(d['tonal_mean_correct'])} | {100*d['band_mean_gain']:.2f} | {'；'.join(d['failures']) or '无'} |")
    lines+=['', '开发集合法窄带目标的回退触发率约99%，说明“频谱集中”不能直接解释为干扰。例如方位边缘+早反射，β=.75正确率50.64%，回退后46.92%，限幅后50.52%。因此未选择单频平均正确率更高、却损害目标控制组的回退方案。']
    lines+=['', '## 新验证集总体结果', '',
        '下表是范围内条件等权平均正确率，各噪声包含3方向×3传播条件。正确率分母含拒绝/等待帧；仅误差≤10°的新鲜输出计正确。不同噪声的频谱和带内SNR不等，不按绝对正确率排名噪声难易。',
        '', '| 输入类型 | 原PHAT/% | β=.75/% | 保护后/% | 保护−β/百分点 |', '|---|---:|---:|---:|---:|']
    overview=[]
    for noise in s.s.read(s.HERE/'protocol.json')['validation_noises']:
        conditions=sorted({r['condition'] for r in pool if r['allowed'] and r['condition'].startswith(noise+'__')})
        means={m:float(np.mean([ix[c,m]['active_correct_within10_rate'] for c in conditions])) for m in ['phat','beta075',name]}
        overview.append(dict(noise=noise,**means))
        lines.append(f"| {noise} | {pct(means['phat'])} | {pct(means['beta075'])} | {pct(means[name])} | {100*(means[name]-means['beta075']):+.2f} |")
    lines+=['', '验证未通过项（按预先门限，不追改参数）：'+('；'.join(dec['failures']) or '无'),
        '', '## 全部范围内条件', '',
        '| 条件 | PHAT正确/% | β正确/% | 保护正确/% | 保护−β三种子差值范围/百分点 | 原βP95/° | 保护P95/° | 保护触发率/% |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in sorted({r['condition'] for r in pool if r['allowed']}):
        a,b,g=[ix[c,m] for m in ['phat','beta075',name]];ds=[]
        for seed in s.s.read(s.HERE/'protocol.json')['validation_seeds']:
            p={r['method']:r for r in per if r['condition']==c and int(r['seed'])==seed}
            ds.append(100*(float(p[name]['active_correct_within10_rate'])-float(p['beta075']['active_correct_within10_rate'])))
        lines.append(f"| {c} | {pct(a['active_correct_within10_rate'])} | {pct(b['active_correct_within10_rate'])} | {pct(g['active_correct_within10_rate'])} | {min(ds):+.2f}～{max(ds):+.2f} | {num(b['p95_error_deg'])} | {num(g['p95_error_deg'])} | {100*g['active_guard_trigger']/g['active_frames']:.2f} |")
    lines+=['', 'cap150如被选择，触发率列恒为0，因为它连续限幅而非开关；不应据此说保护未生效。P95仅在新鲜输出上统计，不能脱离覆盖率。',
        '', '## 范围外声源与真正缺席', '',
        'outside32的实际声源在32°，超出允许锥2°；以下为该声源稳定在场时错误产生范围内新鲜输出的比例，不将其算成目标正确率。',
        '', '| 条件 | PHAT错误输出/% | β错误输出/% | 保护错误输出/% |', '|---|---:|---:|---:|']
    for c in sorted({r['condition'] for r in pool if not r['allowed']}):
        a,b,g=[ix[c,m] for m in ['phat','beta075',name]]
        lines.append(f"| {c} | {pct(a['active_fresh_rate'])} | {pct(b['active_fresh_rate'])} | {pct(g['active_fresh_rate'])} |")
    totals={}
    for m in ['phat','beta075',name]:
        group=[r for r in pool if r['method']==m]
        t={k:sum(r[k] for r in group) for k in ['absent_frames','absent_fresh_false_outputs','absent_hold_display_frames','hold_frames']};totals[m]=t
        lines.append(f"\n{m}：真正缺席误输出 {t['absent_fresh_false_outputs']}/{t['absent_frames']}；缺席HOLD旧显示 {t['absent_hold_display_frames']} 帧；全程HOLD {t['hold_frames']} 帧。")
    lines+=['', '## 捕获与延迟', '',
        '每条件6次发声。下面只统计范围内条件；同条件/种子/次序两方法均有正确输出时才计算配对延迟差，未捕获单列。延迟为发声起点至稳定接收段首个正确输出，含传播与分帧，不是硬件处理时间。',
        '', '| 类型 | β捕获成功/事件 | 保护成功/事件 | 共同成功 | 差值中位数/ms | 最大变慢/ms |', '|---|---:|---:|---:|---:|---:|']
    latency=[]
    for noise in s.s.read(s.HERE/'protocol.json')['validation_noises']:
        old={(r['condition'],r['seed'],r['episode']):r for r in lat if r['allowed']=='True' and r['condition'].startswith(noise+'__') and r['method']=='beta075'}
        new={(r['condition'],r['seed'],r['episode']):r for r in lat if r['allowed']=='True' and r['condition'].startswith(noise+'__') and r['method']==name}
        delta=[float(new[k]['latency_ms'])-float(v['latency_ms']) for k,v in old.items() if v['found']==new[k]['found']=='True']
        row=dict(noise=noise,events=len(old),old_success=sum(v['found']=='True' for v in old.values()),new_success=sum(v['found']=='True' for v in new.values()),common=len(delta),median_delta=float(np.median(delta)) if delta else None,max_delta=max(delta) if delta else None)
        latency.append(row)
        lines.append(f"| {noise} | {row['old_success']}/{len(old)} | {row['new_success']}/{len(old)} | {len(delta)} | {num(row['median_delta'])} | {num(row['max_delta'])} |")
    lines+=['', '## 方法限制与交付', '',
        '开发96次、验证216次配对试验，开发种子2026091300–1302，验证2026091400–1402，均不与前研究复用。开发单频1kHz；验证改为700/1600/2800Hz并加入合成长尾声。front=(0°,10°)、az_edge=(28°,0°)、el_edge=(0°,28°)、outside32=(32°,0°)。每次5s，两次发声，1024/512分帧，原5/12、30°及HOLD规则固定。',
        'narrow_target为合法800–1400Hz带限目标，加0.1RMS同频带噪声；它只是一个窄带目标控制，不覆盖纯音、谐波音乐或真实语音的全部形态。其他目标为原宽带探测声，背景噪声全频RMS1；各条件不保证相同带内SNR。',
        '真实发声先门控再因果卷积，真正缺席按完整RIR支持判定，残响尾声属于过渡；不以发声停止立即当作目标缺席。每算法共享同一输入。标签和方向真值只在定位与跟踪更新后用于评分。',
        '3个种子只支持描述性检查，重叠帧不是独立样本；没有实测RIR、实时计算预算或实板验证。频谱集中度不是干扰身份识别：合法目标也可能集中。若门限通过，仍须A复核后决定下一阶段，不自动部署。',
        '本轮只在research/narrowband-guard-01新增文件；原517个文件保持哈希不变，默认算法未改，未提交/推送/合入。指定复核人拓芙（A），本轮尚未取得批准。',
        '下一轮应另设开发方案，优先检查不同子频带的时延一致性及边界候选可信度：仅按频谱集中度回退会误伤目标，仅限制幅度仍可能保留错误相位贡献。本次700/1600/2800Hz结果已经看过，应作为固定失败参照，不能继续用于声称新方案独立验证。没有在本轮追加调参或扩大方向范围。',
        '172项测试通过；audit.json记录全量落盘标签、角度、计数、延迟、选择锁定和哈希检查，并重建10份输入。门限计算复用了冻结函数，审计如实注明，未宣称完全独立的门限实现。']
    return '\n'.join(lines)+'\n',dict(selected=name,development_passed=selection['development_passed'],validation_passed=dec['passed'],overview=overview,totals=totals,latency=latency)

if __name__=='__main__':
    text,data=render()
    for name,value in [('REPORT.md',text),('diagnostics.json',None)]:
        path=s.HERE/name
        if path.exists():raise ValueError('output exists')
        if value is None:s.s.entry.write_json(path,data)
        else:path.write_text(value,encoding='utf-8')
    print(data)
