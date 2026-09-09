# Revised historical consistency check; paired with a live audit by run_all.
import sys
from common import ROOT, verify_package
sys.path.insert(0,str(ROOT/'research/subband-confidence-01'))
"""Read-only final verification, including failure claims and immutable references."""
import json
import report
import run_study as s

def check():
    verify_package();a=s.s.read(s.HERE/'audit.json');assert a['status']=='PASS'
    assert a['auditor_sha256']==s.s.entry.sha256(s.HERE/'audit.py')
    r=s.s.read(s.HERE/'evidence/run.json');assert r['trials']==144 and r['acoustic_frames']==67248
    assert r['protocol_sha256']==s.s.entry.sha256(s.HERE/'protocol.json')
    for n,h in r['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    for n,h in r['artifacts'].items():assert s.s.entry.sha256(s.HERE/'evidence'/n)==h,n
    t=s.s.read(s.HERE/'tests/validation.json');assert t['status']=='PASS' and t['tests']==173
    for n,h in t['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    text,data=report.render();assert text==(s.HERE/'REPORT.md').read_text(encoding='utf-8')
    assert data==s.s.read(s.HERE/'diagnostics.json')
    before=data['totals']['cap150_quorum'];after=data['totals']['envelope_quorum']
    assert (before['inside_correct'],after['inside_correct'],before['outside_fresh'],after['outside_fresh'])==(12692,78,127,0)
    assert data['event_totals']['cap150_quorum']==[158,192] and data['event_totals']['envelope_quorum']==[8,192]
    loss=s.s.read(s.HERE/'loss-diagnosis.json');assert loss['source_sha256']==s.s.entry.sha256(s.HERE/'diagnose_loss.py')
    assert loss['counts']['band']['valid_bands_2']==82
    for noise,c in loss['counts'].items():assert sum(c.get('valid_bands_'+str(i),0) for i in range(4))==c['frames']==9234
    assert loss['subband_rejections']['narrow_target:band1']['valid']==loss['subband_rejections']['narrow_target:band2']['valid']==0
    clean=loss['clean_controls'];assert len(clean)==12
    for c in clean:
        if c['room']['name']=='dry':assert c['counts']['valid_bands_3']==c['counts']['frames']==289
        if c['room']['name']=='dry' and c['direction']['name']=='az30':assert c['counts']['boundary_uncertain']==289
    if (s.HERE/'files.json').exists():
        for n,h in s.s.read(s.HERE/'files.json')['files'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    return dict(status='PASS',tests=173,main_trials=144,post_result_controls=12,fixed_prior_files=len(s.s.read(s.HERE/'fixed-files.json')),
        research_decision='Do not use these fixed screens as general candidate gates; diagnostic only',report_reproducible=True,checker_sha256=s.s.entry.sha256(__file__))

