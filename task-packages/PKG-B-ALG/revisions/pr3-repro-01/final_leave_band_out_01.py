# Revised historical consistency check; paired with a live audit by run_all.
import sys
from common import ROOT, verify_package
sys.path.insert(0,str(ROOT/'research/leave-band-out-01'))
import json
import run_study as s
import sys
sys.path.insert(0,str(s.HERE))
import report

def check():
    verify_package();a=s.s.read(s.HERE/'audit.json');assert a['status']=='PASS'
    assert a['auditor_sha256']==s.s.entry.sha256(s.HERE/'audit.py')
    r=s.s.read(s.HERE/'evidence/run.json');assert r['trials']==144 and r['acoustic_frames']==67248 and r['method_rows']==268992
    assert r['protocol_sha256']==s.s.entry.sha256(s.HERE/'protocol.json')
    for n,h in r['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    for n,h in r['artifacts'].items():assert s.s.entry.sha256(s.HERE/'evidence'/n)==h,n
    t=s.s.read(s.HERE/'tests/validation.json');assert t['status']=='PASS' and t['tests']==173
    for n,h in t['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    text,data=report.render();assert text==(s.HERE/'REPORT.md').read_text(encoding='utf-8')
    assert data==s.s.read(s.HERE/'diagnostics.json')
    assert [data['totals'][m]['correct'] for m in ['cap150_quorum','split_strict_quorum','loo_strict_quorum','loo_known_only_quorum']]==[11781,568,9544,10609]
    assert data['totals']['cap150_quorum']['outside_fresh']==119 and data['totals']['loo_known_only_quorum']['outside_fresh']==57
    availability=s.s.read(s.HERE/'availability.json')
    assert availability['source_sha256']==s.s.entry.sha256(s.HERE/'availability.py')
    assert availability['counts']['narrow_target']['frames_all_comparisons_remove_zero_bins']==5622
    if (s.HERE/'files.json').exists():
        for n,h in s.s.read(s.HERE/'files.json')['files'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    return dict(status='PASS',trials=144,tests=173,frozen_prior_files=len(s.s.read(s.HERE/'fixed-files.json')),report_reproducible=True,
        source_lock=True,checker_sha256=s.s.entry.sha256(__file__))
