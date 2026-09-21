import copy
import importlib.util
import json
from pathlib import Path

root=Path('F:/NUEC/r/ready/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918')
s=importlib.util.spec_from_file_location('check',root/'check_readiness_20260921.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
cfg=json.loads((root/'service-budget-20260921.json').read_text(encoding='utf-8'))
results=[]
def check(name,condition):
    assert condition,name
    results.append(name)

c=copy.deepcopy(cfg)
for v in c['services']: v.update(clock_hz=1500,cycles_per_hop=1)
r=m.evaluate(c)
check('exact_deadline_equality',r['conditional_serial_seconds']=='4/375' and r['conditional_deadline_met'] is True)
c['services'][-1]['cycles_per_hop']=2
check('one_cycle_late',m.evaluate(c)['conditional_deadline_met'] is False)
c['services'][-1]['clock_hz']=None
check('unknown_clock_blocks',m.evaluate(c)['conditional_serial_seconds'] is None)
c=copy.deepcopy(cfg)
c['queue'].update(initial_packets=2,burst_packets=1,max_blackout_ns=26041666,minimum_service_packets_per_second=192)
r=m.evaluate(c)
check('queue_integer_rounding_below',r['queue_conditional_peak_packets']==8 and r['queue_conditional_sufficient'] is True)
c['queue']['max_blackout_ns']+=1
r=m.evaluate(c)
check('queue_integer_rounding_above',r['queue_conditional_peak_packets']==9 and r['queue_conditional_sufficient'] is False)
c['queue'].update(max_blackout_ns=0,minimum_service_packets_per_second=191)
check('steady_state_rate_insufficient',m.evaluate(c)['queue_conditional_sufficient'] is False)
c=copy.deepcopy(cfg)
for hop,packets in [(250,1),(251,2),(500,2),(501,3),(512,3)]:
    c['hop_samples']=hop
    check('packet_phase_'+str(hop),m.evaluate(c)['max_full_packet_arrivals_per_hop']==packets)
notes=[]
for field,val in [('burst_packets',-1),('max_blackout_ns',True),('minimum_service_packets_per_second',-10)]:
    c=copy.deepcopy(cfg);c['queue'][field]=val
    r=m.evaluate(c)
    notes.append({'field':field,'invalid_value':val,'queue_result':r['queue_conditional_sufficient'],'status':r['status']})
print(json.dumps({'independent_checks_passed':results,'partial_invalid_queue_input_observations':notes},indent=2))
