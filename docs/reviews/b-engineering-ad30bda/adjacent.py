"""Independent A R1/R2 adjacency controls; no production or numeric imports."""
import argparse,copy,importlib.util,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert not a.out.exists()
pkg=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921'
s=importlib.util.spec_from_file_location('dut',pkg/'trace_scoreboard.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def event(kind,frame=7,**kw):return dict(kind=kind,session='new',frame=frame,**kw)
def row(tick,now,events,**kw):return dict(tick=tick,now=now,session='new',valid=False,ready=True,events=events,**kw)
def trace():
    return [row(0,30,[event('submit',config='frozen',expected=['fft','ifft'])],reset=True),row(1,31,[event('status',unit='fft')]),row(2,35,[event('status',unit='ifft')]),row(3,40,[event('commit',config='frozen',available=35,valid_through=40)])]
cases=[]
def add(name,rows,error=None,units=('fft','ifft')):cases.append((name,rows,error,units))
add('delayed-commit-expiry-equality',trace())
t=trace();t[3]['events'][0]['available']=34;add('completion-minus-one',t,'availability precedes required status visibility')
t=trace();t[2]['events'][0]['available']=0;t[3]['events'][0]['available']=34;add('ignore-forged-status-timestamp',t,'availability precedes required status visibility')
t=trace();t[3]['events'][0]['available']=39;add('availability-between-completion-and-commit',t)
t=trace();t[3]['events'][0]['available']=41;add('availability-after-commit',t,'future or expired commit')
t=trace();t[3]['now']=41;add('expiry-plus-one',t,'future or expired commit')
t=trace();t[2]['events']=[];t[3]['events'].append(event('status',unit='ifft'));t[3]['events'][0]['available']=40;add('commit-listed-before-same-tick-status',t)
t=copy.deepcopy(t);t[3]['events'].append(event('error'));add('same-tick-error-wins-over-reordered-commit',t,'non-atomic commit')
t=trace();t[0]['events'].append(event('submit',frame=8,config='frozen',expected=['fft','ifft']));t[3]['events'] += [event('status',frame=8,unit='fft'),event('status',frame=8,unit='ifft')];add('other-frame-later-status-does-not-raise-bound',t)
fixture=json.loads((pkg/'evidence/run05/checks/valid-trace.json').read_text())
for name,index,key,value,error in [('accepted-source-nan',9,'source_sample',float('nan'),'integer source_sample required'),('held-available-inf',12,'available',float('inf'),'uint64 output available required'),('initial-stall-source-string',11,'source_sample','2','integer source_sample required'),('recovery-available-string',13,'available','10','uint64 output available required')]:
    t=copy.deepcopy(fixture);t[index]['payload'][key]=value;add(name,t,error)
# Physical sample clock advances while a single output is held; do not equate tick/emit/now.
t=copy.deepcopy(fixture)
for r in t[12:]:r['now']+=5
add('physical-time-advances-under-stall',t)
a.out.mkdir(parents=True);results=[]
for name,t,error,units in cases:
    got=None
    try:result=m.check(t,max_stall_ticks=2,expected_units=units)
    except m.TraceError as exc:got=str(exc);result=None
    assert got==error,(name,error,got)
    (a.out/(name+'.json')).write_text(json.dumps(t,indent=2)+'\n')
    results.append(dict(name=name,expected_error=error,actual_error=got,result=result))
out=dict(status='A_ADJACENT_PASS',cases=len(results),rejected=sum(x['actual_error'] is not None for x in results),accepted=sum(x['actual_error'] is None for x in results),results=results,note='NaN/Infinity fixtures are Python JSON decoder robustness probes, not valid production JSON')
(a.out/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='results'}))
