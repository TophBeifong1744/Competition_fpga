"""A independent review runner; only creates a fresh output tree."""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys

PIN = '94e1ae9d2ed263de6160b6c14e97b3dc71392dd0'
TASK = Path('task-packages/PKG-B-ALG/tasks/four-channel-receipt-01')
PKG = Path('task-packages/PKG-B-ALG')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    def git(*argv):
        return subprocess.check_output(['git', *argv], cwd=repo)
    head = git('rev-parse', 'HEAD').decode().strip()
    task = repo/TASK
    fixtures = repo/PKG/'reference/h1-ss-data-draft-0.3/payload/examples/h1'
    original = git('ls-tree', '-r', '--name-only', PIN, '--', str(TASK).replace('\\','/')).decode().splitlines()
    protected = original + [str(PKG/'payload/model/python/h1_reader.py').replace('\\','/')]
    for name in ('code-pattern','restart'):
        protected.extend(str((PKG/'reference/h1-ss-data-draft-0.3/payload/examples/h1')/name/f).replace('\\','/') for f in ('metadata.json','samples.csv'))
    before = {p: digest((repo/p).read_bytes()) for p in protected}
    blob_equal = {p: before[p] == digest(git('show', f'{PIN}:{p}')) for p in protected}
    assert all(blob_equal.values()), blob_equal
    author_hashes = json.loads((task/'evidence/run01/validation.json').read_text(encoding='utf-8-sig'))['source_sha256']
    assert all(digest((repo/p).read_bytes()) == h for p,h in author_hashes.items())
    write_json(out/'preservation-before.json', dict(reviewed_sha=PIN, checkout_sha=head, sha256=before, pinned_blob_equal=blob_equal))
    commands=[]
    def command(label, argv, expected=0):
        result = subprocess.run(argv, cwd=repo, env=env, capture_output=True, text=True, encoding='utf-8')
        (out/(label+'.stdout.txt')).write_text(result.stdout,encoding='utf-8')
        (out/(label+'.stderr.txt')).write_text(result.stderr,encoding='utf-8')
        commands.append(dict(label=label, argv=argv, cwd=str(repo), exit_code=result.returncode, expected=expected))
        assert result.returncode == expected, (label,result.stderr)
        return result
    command('author-tests',[sys.executable,'-B',str(TASK/'test_diagnose.py')])
    command('reader-tests',[sys.executable,'-B',str(PKG/'payload/tb/python/test_h1_reader.py')])
    demo = [sys.executable,'-B',str(TASK/'diagnose.py'),str(fixtures/'code-pattern'),str(fixtures/'restart'),'--out',str(out/'fixture-diagnostics')]
    command('demo',demo)
    command('existing-output-rejected',demo,2)
    report=json.loads((out/'fixture-diagnostics/summary.json').read_text(encoding='utf-8'))
    expected=json.loads((task/'evidence/run01/fixture-diagnostics/summary.json').read_text(encoding='utf-8'))
    root_old=expected['segments'][0]['directory'].split('task-packages')[0]
    def portable(v):
        if isinstance(v,dict):
            return {portable(k):portable(x) for k,x in v.items() if k != 'environment'}
        if isinstance(v,list): return [portable(x) for x in v]
        if isinstance(v,str):
            return v.replace(root_old,'<REPO>/').replace(str(repo)+'\\','<REPO>/').replace('\\','/')
        return v
    assert portable(report)==portable(expected), 'structured fixture results differ'
    old_errors=json.loads((task/'evidence/run01/fixture-diagnostics/errors.json').read_text(encoding='utf-8'))
    new_errors=json.loads((out/'fixture-diagnostics/errors.json').read_text(encoding='utf-8'))
    assert portable(old_errors)==portable(new_errors)
    numerical=[]
    for segment in report['segments']:
        path=Path(segment['directory'])
        with (path/'samples.csv').open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        assert segment['first_sample_id']==rows[0]['sample_id'] and segment['last_sample_id']==rows[-1]['sample_id']
        for key, selected in [('amplitude_all_rows',rows),('amplitude_format_clean_rows',[r for r in rows if int(r['stream_error'])==0])]:
            for a in segment[key]:
                values=[int(row[a['channel']]) for row in selected]
                n=len(values); mean=math.fsum(values)/n
                recomputed=dict(minimum=min(values),maximum=max(values),mean_pcm=mean,
                    rms_pcm=math.sqrt(sum(x*x for x in values)/n),
                    ac_rms_pcm=math.sqrt(math.fsum((x-mean)**2 for x in values)/n),
                    full_scale_code_count=sum(x in (-2**23,2**23-1) for x in values),
                    peak_fullscale=max(abs(x) for x in values)/2**23,
                    zero_code_count=values.count(0))
                diffs={k:abs(a[k]-v) for k,v in recomputed.items()}
                assert all(math.isclose(a[k],v,rel_tol=1e-13,abs_tol=1e-9) for k,v in recomputed.items())
                numerical.append(dict(segment=path.name,selection=key,channel=a['channel'],absolute_difference=diffs))
    spec=importlib.util.spec_from_file_location('a_review_diagnose', task/'diagnose.py')
    d=importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
    meta=json.loads((fixtures/'restart/metadata.json').read_text(encoding='utf-8-sig'))
    cases=out/'cases'; cases.mkdir()
    checks=[]
    def sample(name, rows=None, changes=None, header=None, raw=None):
        path=cases/name;path.mkdir()
        m=copy.deepcopy(meta);m.update(changes or {})
        write_json(path/'metadata.json',m)
        if raw is not None: (path/'samples.csv').write_text(raw,encoding='utf-8')
        else:
            with (path/'samples.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.writer(f);w.writerow(header or d.reader.HEADER)
                w.writerows(rows if rows is not None else [[0,1,2,3,4,0,''],[1,2,3,4,5,0,'']])
        return path
    def run_case(name, inputs, expected_codes=None, **kw):
        source_before={str(p):digest(p.read_bytes()) for folder in inputs if folder.is_dir() for p in folder.iterdir() if p.is_file()}
        r=d.run(inputs,cases/(name+'-out'),**kw)
        assert source_before=={p:digest(Path(p).read_bytes()) for p in source_before}
        if expected_codes is not None:
            assert [s.get('error',{}).get('code') for s in r['segments']]==expected_codes
        assert not r['h2_acceptance'] and not r['four_channel_real_input_verified']
        checks.append(dict(case=name,readable=r['readable'],rejected=r['rejected']))
        return r
    # Whole real-valued correlations, independently evaluated within each segment.
    rows=[[i,i,3*i+7,-i,(i%5)-2,0,''] for i in range(32)]
    rows += [[2**53+17,123,234,345,456,1,'drop;overflow;relock']]
    rows += [[2**53+18+i,100-i,2*i+9,i-100,(i%7)-3,0,''] for i in range(32)]
    r=run_case('gap-separated',[sample('gap',rows)])['segments'][0]
    assert len(r['pair_intervals'])==12
    assert [(x['row_start'],x['row_stop']) for x in r['clean_intervals']]==[(0,32),(33,65)]
    assert r['flagged_rows'][0]==dict(row_index=32,csv_line=34,sample_id=str(2**53+17),pcm=[123,234,345,456],flags=['drop','overflow','relock'])
    assert r['missing_intervals']==[dict(first='32',last=str(2**53+16),count=str(2**53-15))]
    for pair in r['pair_intervals']:
        a,b=(int(s[-1])+1 for s in pair['channels'])
        seq=rows[pair['row_start']:pair['row_stop']]
        x=[row[a] for row in seq];y=[row[b] for row in seq]
        mx=math.fsum(x)/len(x);my=math.fsum(y)/len(y)
        corr=math.fsum((v-mx)*(w-my) for v,w in zip(x,y))/math.sqrt(math.fsum((v-mx)**2 for v in x)*math.fsum((w-my)**2 for w in y))
        assert math.isclose(corr,pair['pearson'],abs_tol=1e-14)
    run_case('geometry-conflict',[sample('geom-base'),sample('geom-change',changes=dict(config_version='new',coordinates_m=[[0,0,0]]*4))],[None,'geometry_conflict'])
    run_case('acquisition-overlap',[sample('acq-base'),sample('acq-repeat')],[None,'acquisition_overlap'])
    r=run_case('same-acquisition-unobserved-gap',[sample('part1'),sample('part2',[[100,1,2,3,4,0,''],[101,2,3,4,5,0,'']])],[None,None])
    assert all(s['missing_intervals']==[] and s['pair_intervals']==[] for s in r['segments'])
    run_case('failed-load-no-registry-pollution',[sample('bad-config',[[0,2**23,2,3,4,0,'']],dict(sample_rate_hz=44100)),sample('good-config')],['integer_range',None])
    for n in (3,6):
        header=['sample_id']+[f'mic{i}' for i in range(n)]+['stream_error','error_flags']
        run_case(f'{n}-channels-rejected',[sample(f'{n}-ch',[[0]+[1]*n+[0,'']],header=header)],['header'])
    for key,value in [('valid_bits',16),('storage_dtype','int16'),('alignment','left')]:
        fmt=copy.deepcopy(meta['sample_format']);fmt[key]=value
        run_case('format-'+key,[sample('fmt-'+key,changes=dict(sample_format=fmt))],['sample_format'])
    for name,rows,code in [('pcm-negative-overflow',[[0,-2**23-1,0,0,0,0,'']],'integer_range'),
                         ('id-overflow',[[2**64,0,0,0,0,0,'']],'integer_range'),
                         ('id-wrap',[[2**64-1,0,0,0,0,0,''],[0,0,0,0,0,0,'']],'id_order')]:
        run_case(name,[sample(name,rows)],[code])
    r=run_case('zero-constant',[sample('zeros',[[i,0,0,0,0,0,''] for i in range(32)])])['segments'][0]
    assert all(p['pearson'] is None and p['exact_equal'] and not p['exact_inverted'] for p in r['pair_intervals'])
    assert len([h for h in r['observations'] if h['code']=='CONSTANT_CLEAN_CHANNEL'])==4
    r=run_case('accepted-is-declaration',[sample('accepted',changes=dict(source_kind='hardware-audio',evidence_level='accepted',acceptance_record='unverified-reference',calibration_status='calibrated',calibration_record='unverified-reference'))])['segments'][0]
    assert r['declared_evidence']=='accepted' and not r['acceptance_verified'] and not r['calibration_verified']
    missing=cases/'missing-directory'
    run_case('missing-input-continue',[missing,sample('after-missing')],['io',None])
    multiplebad=sample('multiple-errors',[[0,2**23,0,0,0,0,''],[0,1,1,1,1,0,'']])
    r=run_case('first-fatal-only',[multiplebad],['integer_range'])['segments'][0]
    assert r['error']['csv_line']==2 and 'amplitude_all_rows' not in r
    protected_input=sample('protected')
    for name,dest in [('same',protected_input),('child',protected_input/'output')]:
        try:d.run([protected_input],dest)
        except ValueError: checks.append(dict(case='output-'+name,result='rejected'))
        else:raise AssertionError(name)
    for name,kw in [('threshold-nan',dict(correlation_threshold=float('nan'))),('threshold-zero',dict(correlation_threshold=0)),('min-one',dict(min_pair_samples=1))]:
        try:d.run([protected_input],cases/(name+'-out'),**kw)
        except ValueError:checks.append(dict(case=name,result='rejected-before-output'))
        else:raise AssertionError(name)
        assert not (cases/(name+'-out')).exists()
    # Flagged yet parseable input exits 0; mixed rejection exits 2 with a report.
    command('mixed-cli',[sys.executable,'-B',str(TASK/'diagnose.py'),str(multiplebad),str(fixtures/'restart'),'--out',str(out/'mixed-cli')],2)
    after={p:digest((repo/p).read_bytes()) for p in protected}
    assert before==after
    differences={f:dict(byte_equal=(task/'evidence/run01/fixture-diagnostics'/f).read_bytes()==(out/'fixture-diagnostics'/f).read_bytes(),original_sha256=digest((task/'evidence/run01/fixture-diagnostics'/f).read_bytes()),rerun_sha256=digest((out/'fixture-diagnostics'/f).read_bytes())) for f in ('summary.json','errors.json','receipt.md')}
    write_json(out/'commands.json',commands)
    write_json(out/'independent-checks.json',checks)
    write_json(out/'numerical-checks.json',numerical)
    write_json(out/'validation.json',dict(status='PASS_LIMITED_DIAGNOSTIC_ONLY',reviewed_sha=PIN,checkout_sha=head,author_tests=15,reader_tests=47,additional_cases=len(checks),original_files_unchanged=before==after,author_source_hashes_match=True,fixture_structured_results_equal_after_path_normalization=True,numerical_comparison='Python integer squares + math.fsum; rel_tol 1e-13 abs_tol 1e-9; correlations abs_tol 1e-14',byte_comparisons=differences,environment=dict(python=platform.python_version(),platform=platform.platform(),numpy=d.np.__version__),h2_acceptance=False))
    print(json.dumps(dict(status='PASS',reviewed_sha=PIN,additional_cases=len(checks),out=str(out))))

if __name__=='__main__':main()
