from pathlib import Path
from fractions import Fraction
import importlib.util,json,copy,hashlib
root=Path('F:/NUEC/r/ready/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918')
p=root/'check_readiness_20260921.py';s=importlib.util.spec_from_file_location('dut',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
cfg=json.loads((root/'service-budget-20260921.json').read_bytes());rows=[]
# Exact packet phases in half-open 512 sample hops; no packet takes fractional storage.
counts=[sum(1 for t in range(512) if (t-phase)%250==0) for phase in range(250)]
assert min(counts)==2 and max(counts)==3
r=m.evaluate(cfg);assert r['max_full_packet_arrivals_per_hop']==max(counts)
rows.append(dict(case='packet_all_250_phases',min=min(counts),max=max(counts),mean_bytes_per_hop=512*32,peak_packet_bytes=3*250*32))
for i in range(16):
 c=copy.deepcopy(cfg)
 for j,x in enumerate(c['services']):x.update(cycles_per_hop=j+1,clock_hz=(j+1)*1000000)
 z=m.evaluate(c);assert z['conditional_serial_seconds']==str(Fraction(16,1000000))
 c['services'][i]['clock_hz']=None;z=m.evaluate(c);assert z['conditional_serial_seconds'] is None and z['conditional_deadline_met'] is None
rows.append(dict(case='mixed_clocks_and_each_unknown',cases=16))
n=0
for initial in (0,1,7,8):
 for burst in (1,2,3):
  for ns in (0,1,5208333,5208334,10416666,10416667,50000000):
   for rate in (191,192,193):
    c=copy.deepcopy(cfg);c['queue'].update(initial_packets=initial,burst_packets=burst,max_blackout_ns=ns,minimum_service_packets_per_second=rate)
    # Independent integer ceiling of 192 packets/s times ns latency.
    peak=initial+burst+(192*ns+999999999)//1000000000
    z=m.evaluate(c);assert z['queue_conditional_peak_packets']==peak
    assert z['queue_conditional_sufficient']==(peak<=8 and rate>=192)
    assert z['status']=='REALTIME_BLOCKED';n+=1
rows.append(dict(case='queue_boundary_grid',cases=n))
for k in ('burst_packets','max_blackout_ns','minimum_service_packets_per_second'):
 c=copy.deepcopy(cfg);c['queue'].update(burst_packets=1,max_blackout_ns=0,minimum_service_packets_per_second=192);c['queue'][k]=None
 assert m.evaluate(c)['queue_conditional_sufficient'] is None
rows.append(dict(case='each_unknown_queue_bound',cases=3))
# Record partial malformed queue behavior without promoting it to a false realtime pass.
c=copy.deepcopy(cfg);c['queue']['burst_packets']=-1
z=m.evaluate(c)
rows.append(dict(case='partial_unknown_with_negative_burst_observation',result=z['queue_conditional_sufficient'],status=z['status'],note='known malformed field is not independently validated until all queue bounds present; never approves capacity'))
out=Path(__file__).with_name('independent-results.json');assert not out.exists()
out.write_text(json.dumps(dict(source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),checks=rows),indent=2)+'\n',encoding='utf-8',newline='\n')
print('PASS phases250 mixed16 queue252 unknown3; partial-malformed observation retained')
