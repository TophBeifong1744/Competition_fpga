"""Build review tables from saved measurements; no candidate fitting."""
from common import HERE,load

def make():
    s=load(HERE/'evidence/run01/summary.json')
    text=['# 候选实际结果与失败\n',
          '全部为八段已参与设计的数据的开发观察；重叠帧不是独立试验。没有修改或挑选阈值后隐藏失败。\n',
          '## 存在门对照\n',
          '目标表只取共同source-mapped区间两端各内缩200ms的完整帧，且排除标记及暂定保护区。该掩码没有测定混响或活动真值，故以下不报准确率/召回率。背景用全段，含未知时刻鼠标点击。\n',
          '|Run|划分|帧|冻结门|去直流|频带绝对|标定+持续|',
          '|---|---|---:|---:|---:|---:|---:|']
    for r in s['reports']:
        v=r['sensitivity']['reported_background' if r['background_operator_label'] else '200'];g=v['gate_pass']
        text.append(f"|{r['capture']}|{r['split']}|{v['frames']}|{g['frozen_baseline']}|{g['dc_only']}|{g['band_absolute']}|{g['band_calibrated_duration']}|")
    text+=['\n去直流不能消除50Hz邻域的低频交流背景；绝对频带门仍在背景全部放行。C3显著减少这些开发背景上的放行，但不证明语音/目标存在，且损失候选语音帧。未调到全部目标放行，也未去掉失败段。\n',
           '## 方向开发观察\n',
           '以下仅对数值一致的原浮点投影，计算与目测标称方向的偏差；不是正式定位误差。N含所有掩码内计划帧，V为数值一致帧，W为V中标称偏差>15°。null表示无输出，不用0°替代。\n',
           '|Run|N|V|V/N|标称偏差P50°|P95°|W/V|W/N|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in s['reports']:
        if r['background_operator_label']:continue
        d=r['sensitivity']['200']['numeric']
        text.append(f"|{r['capture']}|{d['eligible_frames']}|{d['output_frames']}|{d['output_fraction']:.3f}|{d['nominal_deviation_p50_deg']:.2f}|{d['nominal_deviation_p95_deg']:.2f}|{d['nominal_gt15_over_outputs']:.3f}|{d['nominal_gt15_over_eligible']:.3f}|")
    text+=['\n原门+±30°、不加新门的±60°、C3+±60°三种tracker，在上述候选区间均没有fresh输出；C3自动音频在八段全程均回退单麦。不能把0个错向输出解释为方向正确；有效输出为0，P50/P95不可定义。逐帧projection、pair原因、tracker原因和失败示例保存在run01；没有调宽稳定性规则来强行产生角度。解析多音的0/±45°符号单测通过，只说明代码符号约定，不证明物理通道映射。\n',
           '### 候选边界敏感性\n',
           '|Run|内缩ms|帧|C3放行|数值V|标称偏差P50°|P95°|',
           '|---|---:|---:|---:|---:|---:|---:|']
    for r in s['reports']:
        if r['background_operator_label']:continue
        for guard in ['100','200','300']:
            v=r['sensitivity'][guard];d=v['numeric']
            text.append(f"|{r['capture']}|{guard}|{v['frames']}|{v['gate_pass']['band_calibrated_duration']}|{d['output_frames']}|{d['nominal_deviation_p50_deg']:.2f}|{d['nominal_deviation_p95_deg']:.2f}|")
    text+=['\n+45°第二段P50随掩码从约94.6°变到36.1°，说明区间选择影响很大；不能选最好窗口作验收。99样点标记峰差未用于硬件校准、通道补偿或方向真值。\n',
           '## 三路音频与可证实范围\n',
           '每段同一PCM、mic0原时间轴，共同裁剪[8,288242)，288234样点；物理可用时间另加8样点，计算延迟假设0。手动预先用目测0/±45°，背景手动0°，没有搜最好听角度。48份24bit WAV包含24份raw及24份共同增益12预览，逐码回读、削顶均为0。\n',
           '|Run|手动相对mic0电平dB|自动相对mic0电平dB|自动波束贡献样点|',
           '|---|---:|---:|---:|']
    for r in s['reports']:
        a=r['audio'];v=a['descriptive_audio']
        text.append(f"|{r['capture']}|{v['manual']['output_level_change_db_vs_mic0']:.3f}|{v['automatic']['output_level_change_db_vs_mic0']:.3f}|{a['beam_contribution_samples']}|")
    text+=['\n电平降低同时可能降低目标、背景和混响，绝非SNR增益。当前自动与单麦逐样点相同，是未锁定后的安全回退，不能把这组音频说成自动增强。手动结果可用于隔离波束本身限制；40mm小阵列对低频共同成分通常分辨力有限，线性插值本身也有频率衰减。未取得用户新试听，不借用旧录音“差不多清楚”的反馈。\n',
           '## 未关闭项\n',
           '正式语音/目标判断、精确方向/活动真值、可测音频收益、全八段整数链与AMD逐码对应、完整FPGA周期/内存/CDC和实板仍未通过。新gate整数探针最大相对频带功率差约0.389%，保留为量化差异；原run05、S1、计时入口、八段格式批准只引用，没有重跑或扩大。\n']
    (HERE/'RESULTS.md').write_text('\n'.join(text).rstrip()+'\n',encoding='utf-8')
    listen=['# 固定增益三路试听\n','统一播放设备与音量；预览全部增益12，不单独调一条音量后比较。本轮尚未试听，自动=单麦是实际结果。全部文件包含标记，听标记响不代表正文改善；正文候选区间见各段audio.json，不将标记或未校准尾响用于评分。\n','|Run|单麦|手动|自动|','|---|---|---|---|']
    for r in s['reports']:
        name=r['capture'];links=[f'[{label}](evidence/run01/audio/{name}-{branch}-preview.wav)' for label,branch in [('单麦','single'),('手动','manual'),('自动','automatic')]]
        listen.append('|'+name+'|'+'|'.join(links)+'|')
    (HERE/'LISTEN.md').write_text('\n'.join(listen)+'\n',encoding='utf-8')
if __name__=='__main__':make()
