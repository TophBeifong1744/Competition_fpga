"""Reviewer-owned counterexamples; does not modify candidate or golden."""
import argparse, copy, importlib.util, json, pathlib
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
assert not a.out.exists()
pkg=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/engineering-closeout-20260921'
s=importlib.util.spec_from_file_location('review_trace',pkg/'trace_scoreboard.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
base=json.loads((pkg/'evidence/run05/checks/valid-trace.json').read_text())
cases={}
bad=copy.deepcopy(base);bad[3]['events'][1]['available']=0;cases['available_before_final_status']=bad
bad=copy.deepcopy(base);bad[9]['payload']['source_sample']=0.0;bad[9]['payload']['available']=8.0;cases['float_sample_identity']=bad
bad=copy.deepcopy(base);bad[0]['events'][0]['expected']=['fft'];cases['weakened_expected_control']=bad
bad=copy.deepcopy(base);bad[12]['payload']['pcm']=0;cases['changed_stall_control']=bad
results={}
for name,rows in cases.items():
    try: result=m.check(rows,max_stall_ticks=2,expected_units=('fft','ifft'))
    except m.TraceError as e: results[name]={'accepted':False,'reason':str(e)}
    else: results[name]={'accepted':True,'result':result}
a.out.mkdir(parents=True)
for name,rows in cases.items(): (a.out/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
(a.out/'result.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
