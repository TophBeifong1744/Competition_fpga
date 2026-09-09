# Revised historical consistency check; paired with a live audit by run_all.
import sys
from common import ROOT, verify_package
sys.path.insert(0,str(ROOT/'research/tonal-edge-01'))
"""Read-only final consistency check; emits JSON to stdout."""
import json
from collections import defaultdict
import analyze as a
import report as r
import study as d

def check():
    fixed=d.s.read(d.HERE/'fixed-files.json')
    verify_package()
    run=d.s.read(d.HERE/'evidence-run-02/run.json')
    assert run['trials']==81 and run['active_method_rows']==43200
    assert run['protocol_sha256']==d.s.entry.sha256(d.HERE/'protocol.json')
    assert run['source_sha256']==d.s.entry.sha256(d.HERE/'study.py')
    for n,h in run['artifacts'].items():assert d.s.entry.sha256(d.HERE/'evidence-run-02'/n)==h,n
    tests=d.s.read(d.HERE/'tests/validation.json');assert tests['status']=='PASS' and tests['tests']==170
    for n,h in tests['source_sha256'].items():assert d.s.entry.sha256(d.HERE/n)==h
    for n,h in tests['prior_sources_sha256'].items():assert d.s.entry.sha256(d.ROOT/n)==h
    analysis=d.s.read(d.HERE/'analysis.json');assert analysis['auditor_sha256']==d.s.entry.sha256(d.HERE/'analyze.py')
    assert analysis['prior_method_rows_matched']==28800
    groups=defaultdict(list)
    for x in a.readrows(d.HERE/'evidence-run-02/frames.csv'):groups[x['condition'],x['intervention'],x['beta']].append(x)
    for x in analysis['summaries']:
        expected=a.aggregate(groups[x['condition'],x['intervention'],x['beta']])
        for k,v in expected.items():assert x[k]==v,k
    ss=analysis['summaries'];ix={(x['condition'],x['intervention'],x['beta']):x for x in ss}
    for c in {x['condition'] for x in ss}:
        x,y=ix[c,'original_tone','1'],ix[c,'original_tone','0.75']
        assert y['pair_rmse_mean']>x['pair_rmse_mean'] and y['tone_weight_share_mean']>x['tone_weight_share_mean']
        x,y=ix[c,'equal_rms_band','1'],ix[c,'equal_rms_band','0.75']
        assert y['correct']>x['correct']
    totals={b:{k:sum(x[k] for x in ss if x['beta']==b and x['intervention']=='original_tone' and not x['condition'].startswith('front')) for k in ['frames','correct','wide_correct','outside','rejected','waiting']} for b in ['1','0.75']}
    assert totals['1']==dict(frames=4800,correct=3786,wide_correct=4739,outside=942,rejected=22,waiting=50)
    assert totals['0.75']==dict(frames=4800,correct=3598,wide_correct=4716,outside=1100,rejected=44,waiting=58)
    assert r.render()==(d.HERE/'REPORT.md').read_text(encoding='utf-8')
    if (d.HERE/'files.json').exists():
        for n,h in d.s.read(d.HERE/'files.json')['files'].items():assert d.s.entry.sha256(d.HERE/n)==h,n
    return dict(status='PASS',prior_files_unchanged=len(fixed),tests=170,trials=81,active_rows=43200,prior_rows_matched=28800,edge_totals=totals,
        checks='Frozen files; trial artifacts and source hashes; test sources; recomputed pooled statistics; headline numerical claims; report reproducibility; incremental manifest when present.',checker_sha256=d.s.entry.sha256(__file__))

