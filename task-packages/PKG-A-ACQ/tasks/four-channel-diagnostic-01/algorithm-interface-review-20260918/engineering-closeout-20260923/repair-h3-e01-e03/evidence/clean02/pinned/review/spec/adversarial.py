"""B independent spec probes; never modifies author evidence."""
from pathlib import Path
import importlib.util, sys, json, hashlib

OUT = Path(__file__).resolve().parent
BASE = Path('F:/NUEC/review-worktrees')
SUFFIX = Path('task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918')
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
ep = BASE/'review-h3-engineering-0abdc91'/SUFFIX/'engineering-closeout-20260923/source/engineering_model.py'
lp = BASE/'review-h3-logic-f879a54'/SUFFIX/'increment-20260923/source/logic_adapter.py'
e, l = load('engineering_probe', ep), load('logic_probe', lp)
results = {'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ep,lp)}, 'cases': []}

# Legal immutable string API inputs: no malicious input types required.
m=e.Results(); m.start()
k=m.submit(0,1023,512,'configA')
first=m.finish(k,1024,'configA',status=True)
m.barrier('CLIP'); m.begin_clean_interval()
late=m.finish(k,1024,'configA',status=True,error=True)
k2=m.submit(1,2047,512,'configA')
second=m.finish(k2,2048,'configA',status=True)
results['cases'].append(dict(name='committed_then_clip_then_late_error', expected='historical commit preserved; late fault fail-stops; next submit rejected', first=first, late=late, failed=m.failed, active=m.active, subsequent_commit=second, audit=m.audit, finding=True))

m=e.Results();m.start()
k=m.submit(0,1023,512,'configA')
first=m.finish(k,1024,'configA',status=True)
k2=m.submit(1,1535,512,'configB')
second=m.finish(k2,1536,'configB',status=True)
results['cases'].append(dict(name='configuration_changed_within_one_epoch', expected='reject configuration change until new session', first=first, second=second, keys=[k,k2], finding=True))

m=e.Results();m.start();binding={'config':'A','numeric':'fixed4'}
k=m.submit(0,1023,512,binding);binding['config']='B'
actual=m.finish(k,1024,{'config':'B','numeric':'fixed4'},status=True)
results['cases'].append(dict(name='mutable_binding_changes_submitted_snapshot', expected='frozen submitted binding remains A; B rejected', actual=actual, stored=m.entries[k]['bindings'], finding=True, note='API does not restrict binding type; main session-change probe also uses only author-style immutable strings'))

# Correct baseline remains fail-stop without intervening revocation.
m=e.Results();m.start();k=m.submit(0,1023,512,'A');m.finish(k,1024,'A',status=True)
m.finish(k,1024,'A',error=True)
results['cases'].append(dict(name='control_direct_post_commit_fault', expected=True, failed=m.failed, passed=m.failed))

# Lower-bound/malformed time checks in task1 are recorded as scope observations,
# not independent blockers: availability trusted mapping contract is external.
cases=[(1023,512,100),(1023,512,1535),(1023,512,1536)]
results['logic_ttl_observations']=[dict(last_id=a,ttl=b,available=c,result=l.commit_decision(last_id=a,ttl=b,available=c)) for a,b,c in cases]
dest=OUT/'adversarial-results.json'
if dest.exists(): raise RuntimeError('refuse overwrite')
dest.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
