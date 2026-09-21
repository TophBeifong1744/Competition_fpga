"""Independent B spec regression for a7f70c5. Source remains frozen."""
from pathlib import Path
import importlib.util,sys,hashlib,json,traceback
P=Path('F:/NUEC/r/h3r/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/engineering-closeout-20260923/repair-h3-e01-e03/source/results.py')
s=importlib.util.spec_from_file_location('repair_spec_probe',P);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
rows=[]
def test(name,fn):
    try: detail=fn();rows.append(dict(name=name,result='PASS',detail=detail))
    except Exception: rows.append(dict(name=name,result='FAIL',traceback=traceback.format_exc()))
def reject(fn):
    try:fn()
    except ValueError as exc:return str(exc)
    raise AssertionError('expected ValueError')
def setup():
    x=m.Results();x.start();k=x.submit(0,1023,512,'A');assert x.finish(k,1023,'A',status=True)=='COMMITTED';return x,k
def history_case(barriers):
    x,k=setup()
    for reason in barriers:
        x.barrier(reason)
        if reason not in ('STOP','RESET'):x.begin_clean_interval()
    assert x.entries[k]['ever_committed']
    x.finish(k,2048,'A',error=True)
    assert x.failed and not x.active
    assert ('LATE_ERROR',k) in x.audit
    assert reject(lambda:x.submit(99,4095,512,'A'))=='IDENTITY'
    return dict(barriers=barriers,audit=x.audit)
for seq in [('CLIP',),('DROP',),('CLIP','DROP'),('STOP',),('RESET',),('CLIP','STOP'),('DROP','RESET'),('STOP','RESET')]:
    test('historical_commit/'+','.join(seq),lambda seq=seq:history_case(seq))
def old_epoch(reason,committed):
    x=m.Results();x.start();old=x.submit(0,1023,512,'A')
    if committed:x.finish(old,1023,'A',status=True)
    x.barrier(reason);x.start();new=x.submit(0,1023,512,'B')
    x.finish(old,1024,'A',error=True)
    assert not x.failed and x.active
    assert x.entries[old]['ever_committed']==committed
    assert x.finish(new,1024,'B',status=True)=='COMMITTED'
    assert ('OLD_SESSION_LATE_ERROR',old) in x.audit
    return dict(old=old,new=new,old_was_committed=committed)
for reason in ('STOP','RESET'):
    for committed in (False,True):test(f'old_epoch/{reason}/{committed}',lambda reason=reason,committed=committed:old_epoch(reason,committed))
def current_stop_error():
    x,k=setup();x.finish(k,1024,'A',stop=True,error=True)
    assert x.failed and x.entries[k]['ever_committed']
    assert ('LATE_ERROR',k) in x.audit
    return x.audit
test('current_stop_and_error',current_stop_error)
def three_epochs():
    x,first=setup();x.barrier('STOP');x.start();second=x.submit(0,1023,512,'B');x.finish(second,1024,'B',status=True)
    x.barrier('RESET');x.start();third=x.submit(0,1023,512,'C')
    for key,cfg in [(first,'A'),(second,'B'),(first,'A')]:x.finish(key,1024,cfg,error=True)
    assert not x.failed and x.finish(third,1024,'C',status=True)=='COMMITTED'
    return dict(epoch=x.epoch,audit=x.audit)
test('multiple_old_epoch_callbacks',three_epochs)
def nested():
    a={'x':[{'k':(b'a',True,None,17)},[1,2]],'tag':'A'}
    b={'tag':'A','x':[{'k':(b'a',True,None,17)},[1,2]]}
    x=m.Results();x.start();k=x.submit(0,1023,512,a)
    snapshot=x.entries[k]['bindings'];a['x'][0]['k']=(b'b',False,None,18);a['x'][1].append(3)
    assert x.entries[k]['bindings']==snapshot==m.freeze(b)
    assert reject(lambda:x.submit(1,1535,512,a))=='SESSION_CONFIG_CHANGE'
    assert x.finish(k,1024,b,status=True)=='COMMITTED'
    x.barrier('CLIP');x.begin_clean_interval()
    assert reject(lambda:x.submit(1,1535,512,a))=='SESSION_CONFIG_CHANGE'
    k2=x.submit(1,1535,512,b);assert x.finish(k2,1536,b,status=True)=='COMMITTED'
    x.barrier('STOP');x.start();k3=x.submit(0,1535,512,a);assert x.finish(k3,1536,a,status=True)=='COMMITTED'
    return dict(snapshot_stable=True,new_session_allows_change=True)
test('nested_snapshot_aliases_and_dict_order',nested)
for original,changed,label in [(True,1,'bool_vs_int'),([1],(1,),'list_vs_tuple'),('A',b'A','str_vs_bytes'),(None,'None','null_vs_string')]:
    def typed(original=original,changed=changed):
        x=m.Results();x.start();x.submit(0,1023,512,original)
        assert reject(lambda:x.submit(1,1535,512,changed))=='SESSION_CONFIG_CHANGE'
        return dict(type_a=type(original).__name__,type_b=type(changed).__name__)
    test('typed_binding/'+label,typed)
def unsupported():
    x=m.Results();x.start()
    for value in (1.5,{1:'A'},{'A':set([1])},bytearray(b'A')):
        assert reject(lambda value=value:x.submit(0,1023,512,value))=='UNSUPPORTED_BINDING'
    k=x.submit(0,1023,512,'A');assert x.finish(k,1024,'A',status=True)=='COMMITTED'
    return 'unsupported types rejected without poisoning first valid submit'
test('unsupported_binding_failure_atomicity',unsupported)
report=dict(sha='a7f70c5149a6503effdbbf16a9903d42c2d39e6d',source=str(P),source_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),cases=rows,pass_count=sum(r['result']=='PASS' for r in rows),fail_count=sum(r['result']=='FAIL' for r in rows))
dest=Path(__file__).with_name('results.json')
if dest.exists():raise RuntimeError('refuse overwrite')
dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2,ensure_ascii=False))
sys.exit(bool(report['fail_count']))
