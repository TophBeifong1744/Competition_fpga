"""Compare independent run to published run05; no frozen-file mutation."""
import argparse, hashlib, json, math, pathlib
from fractions import Fraction
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert not a.out.exists()
author=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921/evidence/run05'
stats={'strict_leaves':0,'float_differences':0,'max_float_difference':0.0}
float_fields={'reference_q8_float','original_error_codes','candidate_error_codes','max_candidate_error_codes','max_original_error_codes','historical_slots_seconds','hop_seconds'}
def eq(x,y,path=()):
    assert type(x) is type(y),path
    if isinstance(x,dict):
        assert x.keys()==y.keys(),path
        for k in x:eq(x[k],y[k],path+(k,))
    elif isinstance(x,list):
        assert len(x)==len(y),path
        for i,(u,v) in enumerate(zip(x,y)):eq(u,v,path+(i,))
    elif isinstance(x,float) and path[-1] in float_fields:
        assert math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=1e-10,rel_tol=1e-12),path
        stats['float_differences']+=x!=y;stats['max_float_difference']=max(stats['max_float_difference'],abs(x-y))
    else:assert x==y,path;stats['strict_leaves']+=1
files=[]
for f in sorted((a.run/'checks').glob('*.json')):
    rel=f.relative_to(a.run);g=author/rel;eq(json.loads(f.read_text()),json.loads(g.read_text()))
    files.append({'path':rel.as_posix(),'bytes_equal':f.read_bytes()==g.read_bytes(),'reviewer_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
eq(json.loads((a.run/'budget.json').read_text()),json.loads((author/'budget.json').read_text()))
expected=json.loads((author/'runner.json').read_text());actual=json.loads((a.run/'runner.json').read_text());assert actual['source_sha256']==expected['source_sha256'];assert [x['exit_code'] for x in actual['commands']]==[0,0,0]
# Closed-form unrolled infinity-norm recurrence including <=1 shift error/step.
factors=[1+Fraction(1,2**i) for i in range(24)]
def product(xs):
    result=Fraction(1)
    for x in xs:result*=x
    return result
bound=(2**24-1)*product(factors)+sum((product(factors[i+1:]) for i in range(24)),Fraction(0))
assert math.ceil(bound)<=80001546<2**27
result=dict(status='PASS',comparison=stats,checks_files=files,budget_semantic_equal=True,runner_source_equal=True,runner_paths_not_byte_compared=True,independent_xy_upper=math.ceil(bound),s28_contains=True)
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks_files'},indent=2))
