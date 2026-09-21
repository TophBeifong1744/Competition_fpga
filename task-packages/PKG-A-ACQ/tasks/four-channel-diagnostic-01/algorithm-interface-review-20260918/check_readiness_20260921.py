"""Read-only exact-source binding and A budget arithmetic; never hardware signoff."""
import argparse
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
A = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
B = 'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/'
IDS = ('capture_dma_cache_copy', 'accepted_row_frame', 'mean_two_windows', 'fft8',
       'fixed4', 'gate_power_state', 'cross_mask_phat', 'conjugate_ifft6', 'lag',
       'doa_cordic_tracker', 'rom_control', 'das_two_beams', 'config_status_commit',
       'arbitration_cdc_reset', 'output_backpressure', 'audit_drain')
# Keep the list explicit below: version identities must not follow moving branches.
PINS = [( '0abdc91c57787b7c868a797b88f35129de169faf', A+'engineering-closeout-20260923/'+p)
        for p in ('ROUTE.md','NUMERIC.md','BUDGET.md')]
PINS += [
 ('fbbaa161098582ba1e5e112b86d39533769bb3e7', A+'ps-semantic-bridge-candidate-01/MEMORY.md'),
 ('ca512a8be7978ab6ca2ade3d5e0b922e53a89c79', A+'ps-semantic-bridge-repair-01/README.md'),
 ('a7f70c5149a6503effdbbf16a9903d42c2d39e6d', A+'engineering-closeout-20260923/repair-h3-e01-e03/README.md'),
 ('268e52627d091b8909890b43586c70564563132e', B+'dynamic-das-20260921/README.md')]
PINS += [('d3d2a3d4e78932830bf12bd84c0517b0a2092872', B+'engineering-closeout-20260921/'+p)
         for p in ('CONTRACT.md','FLOW.md','BUDGET.md','budget_config.json')]


def integer(v, positive=False):
    if type(v) is not int or v < (1 if positive else 0):
        raise ValueError('strict nonnegative/positive integer required')
    return v


def ceil_fraction(v):
    return -(-v.numerator // v.denominator)


def evaluate(cfg):
    fs=integer(cfg['sample_rate_hz'], True)
    hop=integer(cfg['hop_samples'], True)
    ref=integer(cfg['reference_clock_hz'], True)
    packet=integer(cfg['packet_rows'], True)
    rowbytes=integer(cfg['row_bytes'], True)
    services=cfg['services']
    if [s['id'] for s in services] != list(IDS):
        raise ValueError('missing, duplicate, or reordered service ledger')
    missing=[]
    timeline=[]
    elapsed=Fraction(0)
    for s in services:
        cycles=s['cycles_per_hop']; clock=s['clock_hz']
        if cycles is not None: integer(cycles, True)
        if clock is not None: integer(clock, True)
        if cycles is None or clock is None:
            missing.append(s['id'])
            continue
        duration=Fraction(cycles, clock)
        timeline.append({'id':s['id'],'seconds':str(duration)})
        elapsed+=duration
    full=not missing
    q=cfg['queue']
    capacity=integer(q['capacity_packets'],True)
    initial=integer(q['initial_packets'])
    if initial>capacity or q['full_policy']!='FAIL_STOP_NOT_OVERWRITE':
        raise ValueError('invalid queue occupancy/full policy')
    queue_known=all(q[k] is not None for k in ('burst_packets','max_blackout_ns','minimum_service_packets_per_second'))
    peak=None; sufficient=False
    if queue_known:
        burst=integer(q['burst_packets'])
        blackout=integer(q['max_blackout_ns'])
        rate=integer(q['minimum_service_packets_per_second'],True)
        # Conditional token-bucket arrival + rate-latency service envelope.
        peak=initial+burst+ceil_fraction(Fraction(fs*blackout,packet*10**9))
        sufficient=peak<=capacity and Fraction(rate)>=Fraction(fs,packet)
    return {
        'status':'REALTIME_BLOCKED',
        'claim':'CONDITIONAL_ARITHMETIC_ONLY_NOT_PRODUCTION_APPROVAL',
        'hop_seconds':str(Fraction(hop,fs)),
        'hop_reference_cycles_floor':ref*hop//fs,
        'historical_transform_slots':8*integer(cfg['historical_fft_cycles'],True)+6*integer(cfg['historical_ifft_cycles'],True),
        'input_bytes_per_second':fs*rowbytes,
        'max_full_packet_arrivals_per_hop':ceil_fraction(Fraction(hop,packet)),
        'max_packet_payload_bytes_per_hop':ceil_fraction(Fraction(hop,packet))*packet*rowbytes,
        'conditional_serial_seconds':str(elapsed) if full else None,
        'conditional_deadline_met': elapsed<=Fraction(hop,fs) if full else None,
        'service_durations':timeline,
        'unbounded_services':missing,
        'queue_conditional_peak_packets':peak,
        'queue_conditional_sufficient':sufficient if queue_known else None,
        'queue_model':'arrival burst+rate, service latency+rate; not measured',
        'whole_system_peak_bytes':cfg['memory']['whole_system_peak_bytes'],
        'missing_proofs':cfg['missing_proofs']
    }


def tests(cfg):
    results=[]
    def check(name, condition):
        results.append({'name':name,'pass':bool(condition)})
        if not condition: raise AssertionError(name)
    def reject(name, edit):
        c=copy.deepcopy(cfg); edit(c)
        try: evaluate(c)
        except (ValueError,KeyError): check(name, True)
        else: check(name, False)
    r=evaluate(cfg)
    check('unknown_not_zero',r['conditional_serial_seconds'] is None and r['conditional_deadline_met'] is None)
    check('all16_services_unbounded',len(r['unbounded_services'])==16)
    check('reference_deadline',r['hop_reference_cycles_floor']==1066666)
    check('historical_slots_only',r['historical_transform_slots']==103364 and r['status']=='REALTIME_BLOCKED')
    check('whole_h1_bandwidth',r['input_bytes_per_second']==1536000)
    check('packet_burst',r['max_full_packet_arrivals_per_hop']==3 and r['max_packet_payload_bytes_per_hop']==24000)
    check('unknown_queue',r['queue_conditional_sufficient'] is None)
    check('unknown_memory',r['whole_system_peak_bytes'] is None)
    for value in (-1,0,True,1.5):
        reject('invalid_cycle_'+repr(value),lambda c,v=value:c['services'][0].update(cycles_per_hop=v))
    for value in (-1,0,True,1.5):
        reject('invalid_clock_'+repr(value),lambda c,v=value:c['services'][0].update(clock_hz=v))
    reject('missing_service',lambda c:c['services'].pop())
    reject('duplicate_service',lambda c:c['services'].append(copy.deepcopy(c['services'][0])))
    reject('reordered_service',lambda c:c['services'].reverse())
    reject('invalid_initial_queue',lambda c:c['queue'].update(initial_packets=9))
    reject('overwrite_queue',lambda c:c['queue'].update(full_policy='OVERWRITE'))
    synthetic=copy.deepcopy(cfg)
    for s in synthetic['services']: s.update(clock_hz=100000000,cycles_per_hop=1)
    r=evaluate(synthetic)
    check('finite_hypothesis_not_signoff',r['conditional_deadline_met'] and r['status']=='REALTIME_BLOCKED')
    synthetic['services'][0].update(clock_hz=1000000,cycles_per_hop=10000)
    check('clock_conversion',evaluate(synthetic)['conditional_serial_seconds']==str(Fraction(10000,1000000)+Fraction(15,100000000)))
    synthetic['services'][0]['cycles_per_hop']=20000
    check('deadline_exceeded',evaluate(synthetic)['conditional_deadline_met'] is False)
    synthetic['services'][0]['clock_hz']=None
    check('one_unknown_blocks_total',evaluate(synthetic)['conditional_serial_seconds'] is None)
    q=copy.deepcopy(cfg)
    q['queue'].update(burst_packets=1,max_blackout_ns=0,minimum_service_packets_per_second=192)
    check('conditional_queue_fits',evaluate(q)['queue_conditional_sufficient'] is True)
    q['queue']['initial_packets']=8
    check('initial_occupancy_matters',evaluate(q)['queue_conditional_sufficient'] is False)
    q['queue'].update(initial_packets=0,minimum_service_packets_per_second=191)
    check('slow_service_rejected',evaluate(q)['queue_conditional_sufficient'] is False)
    q['queue'].update(minimum_service_packets_per_second=192,max_blackout_ns=50000000)
    check('blackout_overflow',evaluate(q)['queue_conditional_peak_packets']==11 and evaluate(q)['queue_conditional_sufficient'] is False)
    q['queue']['max_blackout_ns']=None
    check('unknown_blackout',evaluate(q)['queue_conditional_sufficient'] is None)
    return results


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=Path(args.out).resolve()
    if out.exists(): raise SystemExit('REFUSE_EXISTING_OUTPUT')
    out.mkdir(parents=True)
    def save(name,obj): (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save('command.json',{'argv':sys.argv,'executable':sys.executable,'cwd':str(Path.cwd()),'python':platform.python_version()})
    try:
        repo=next(p for p in HERE.parents if (p/'.git').exists())
        bindings=[]
        for sha,path in PINS:
            key=sha+':'+path
            raw=subprocess.check_output(['git','show',key],cwd=repo)
            blob=subprocess.check_output(['git','rev-parse',key],cwd=repo,text=True).strip()
            bindings.append({'commit':sha,'path':path,'blob':blob,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        save('bindings.json',bindings)
        cfg=json.loads((HERE/'service-budget-20260921.json').read_text(encoding='utf-8'))
        checks=tests(cfg); save('tests.json',checks); save('budget.json',evaluate(cfg))
        files=['PRODUCTION-READINESS-20260921.md','PRODUCTION-CONTRACT-20260921.md','GOLDEN-GAPS-20260921.md','service-budget-20260921.json','check_readiness_20260921.py']
        save('source-sha256.json',{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files})
        save('result.json',{'status':'PASS_A_READINESS_CHECKS_NOT_H3','tests':len(checks),'source_bindings':len(bindings),'production':'REALTIME_BLOCKED'})
        save('OUTPUT-SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()})
        print('PASS',len(checks),'checks;',len(bindings),'exact sources; REALTIME_BLOCKED')
    except Exception:
        save('FAILURE.json',{'traceback':traceback.format_exc()})
        raise


if __name__=='__main__': main()
