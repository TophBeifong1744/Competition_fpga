# Revised historical consistency check; paired with a live audit by run_all.
import sys
from common import ROOT, verify_package
sys.path.insert(0,str(ROOT/'research/narrowband-guard-01'))
"""Read-only check of frozen sources, evidence and report before A review."""
import json
import study as s
import report

def check():
    verify_package();audit=s.s.read(s.HERE/'audit.json');assert audit['status']=='PASS'
    assert audit['checker_sha256']==s.s.entry.sha256(s.HERE/'audit.py')
    tests=s.s.read(s.HERE/'tests/validation.json');assert tests['status']=='PASS' and tests['tests']==172
    for n,h in tests['source_sha256'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    selection=s.s.read(s.HERE/'development/selection.json');assert selection['selected']=='cap150'
    assert selection['development_passed'] and not selection['decisions']['fallback035']['passed']
    for phase in ['development','validation']:
        run=s.s.read(s.HERE/phase/'run.json')
        assert run['source_sha256']==selection['source_sha256']
        assert run['protocol_sha256']==selection['protocol_sha256']==s.s.entry.sha256(s.HERE/'protocol.json')
        for n,h in run['artifacts'].items():assert s.s.entry.sha256(s.HERE/phase/n)==h,n
    text,diagnostics=report.render()
    assert text==(s.HERE/'REPORT.md').read_text(encoding='utf-8')
    assert diagnostics==s.s.read(s.HERE/'diagnostics.json')
    if (s.HERE/'files.json').exists():
        for n,h in s.s.read(s.HERE/'files.json')['files'].items():assert s.s.entry.sha256(s.HERE/n)==h,n
    return dict(status='PASS',tests=172,frozen_prior_files=len(s.s.read(s.HERE/'fixed-files.json')),development_trials=96,validation_trials=216,
        selected=selection['selected'],development_passed=selection['development_passed'],validation_passed=diagnostics['validation_passed'],
        report_reproducible=True,source_lock=True,checker_sha256=s.s.entry.sha256(__file__))
