import json,sys
import run_study as s
sys.path.insert(0,str(s.HERE))
import report
import compare_outputs

def check():
    s.verify();a=s.s.read(s.HERE/'audit.json');assert a['status']=='PASS'
    assert a['auditor_sha256']==s.s.entry.sha256(s.HERE/'audit.py')
    r=s.s.read(s.HERE/'evidence/run.json');assert r['trials']==144 and r['acoustic_frames']==67248 and r['method_rows']==201744
    assert r['protocol_sha256']==s.s.entry.sha256(s.HERE/'protocol.json')
    for n,h in r['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    for n,h in r['artifacts'].items():assert s.s.entry.sha256(s.HERE/'evidence'/n)==h,n
    t=s.s.read(s.HERE/'tests/validation.json');assert t['status']=='PASS' and t['tests']==173
    for n,h in t['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    text,data=report.render();assert text==(s.HERE/'REPORT.md').read_text(encoding='utf-8')
    assert data==s.s.read(s.HERE/'diagnostics.json')
    old=data['totals']['old_loo_known_only'];new=data['totals']['effective_known_only']
    assert old==new and new['correct']==11801 and new['outside_fresh']==205
    assert a['transitions']['narrow_target']['stable->unknown']==5443
    assert a['impact_status_counts']['narrow_target']['no_change']==10886
    assert a['category_risk_among_full_incone']['stable']['outside']==563
    comparison=compare_outputs.run();assert comparison==s.s.read(s.HERE/'output-equivalence.json') and comparison['different_pairs']==0
    if (s.HERE/'files.json').exists():
        for n,h in s.s.read(s.HERE/'files.json')['files'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    return dict(status='PASS',trials=144,tests=173,frozen_prior_files=len(s.s.read(s.HERE/'fixed-files.json')),output_pairs_equal=67248,
        report_reproducible=True,source_lock=True,checker_sha256=s.s.entry.sha256(__file__))

if __name__=='__main__':print(json.dumps(check()))
