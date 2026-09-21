"""Recalculate disjoint reference models; never elevate estimates to WCET."""
import argparse
import json
from fractions import Fraction
from pathlib import Path


def calculate(c):
    fs, hop, clock = (c[k] for k in ('sample_rate_hz', 'hop_samples', 'proposed_algorithm_clock_hz'))
    assert all(type(v) is int and v > 0 for v in (fs, hop, clock))
    branches = {}
    for name, branch in c['branches'].items():
        f, i = branch['fft'], branch['ifft']
        assert type(f) is int and type(i) is int and f >= 0 and i >= 0
        cycles = f*c['historical_fft_slot_cycles'] + i*c['historical_ifft_slot_cycles']
        branches[name] = dict(**branch, historical_slots_cycles=cycles,
                              historical_slots_seconds=float(Fraction(cycles, clock)),
                              hypothetical_materialized_transform_bytes=(f+i)*1024*8*2,
                              wcet_seconds=None)
    assert branches['legacy_doa']['historical_slots_cycles'] == 73900
    assert branches['centered_gate_plus_doa']['historical_slots_cycles'] == 103364
    assert len({s['name'] for s in c['services']}) == 13
    # This input contract intentionally contains no certified service bounds.
    # A numeric scenario parameter must not accidentally become a certificate.
    assert all(s['upper'] is None for s in c['services']), 'reviewed finite service evidence required before extending ledger'
    return dict(status='REALTIME_BLOCKED', total_seconds=None,
                hop_seconds=float(Fraction(hop, fs)), proposed_hop_cycles=clock*hop//fs,
                branches=branches, services=c['services'],
                traffic_bytes_per_second=dict(raw_with_ids_flags=32*fs, pcm_int32=16*fs, mono_int32=4*fs),
                memory_models={
                    'B_listed_historical': dict(bytes=107496, scope='listed buffers only; includes old160-byte audio history; no IP internals'),
                    'A_relative_layout': dict(bytes=202816, scope='separate 64-byte aligned logical PS layout, no deployed absolute addresses'),
                    'dynamic_candidate_net': dict(history_s24_bytes=17*4*3, config_rom_s16_bytes=3*4*2,
                                                  config_generic_s17_packed_bytes=27, config_int32_bytes=48,
                                                  rom_net_bytes=92160*3*2, total_deployment_bytes=None),
                    'system_upper_bytes': None},
                queue_contract=dict(required_inputs=['arrival burst','maximum service blackout','minimum sustained service rate',
                                                      'initial occupancy','in_service counts in capacity','full policy'],
                                    capacity_proven=None, note='Two output hops or eight packets alone do not prove bounded operation'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = calculate(json.loads(a.config.read_text(encoding='utf-8')))
    with a.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(result['status'], 'total=null', 'hop_cycles='+str(result['proposed_hop_cycles']))
