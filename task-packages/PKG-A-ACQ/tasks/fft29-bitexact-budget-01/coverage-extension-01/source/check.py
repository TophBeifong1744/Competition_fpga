"""Fail-closed, code-by-code comparison with archived wide29_raw_fft."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np


def table(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path,'rt',encoding='ascii') as f:
        return np.loadtxt(f,delimiter=',',dtype=np.int64,ndmin=2)


def compare(rows, expected, status, jobs):
    count, length, components = expected.shape
    assert length == 1024 and components == 2 and len(jobs) == count
    issues = []
    if rows.shape != (count*length,4):
        return {'pass':False,'issues':['output_shape'],'actual_shape':list(rows.shape)}
    if not np.array_equal(rows[:,0],np.repeat(np.arange(count),length)):
        issues.append('job_order')
    if not np.array_equal(rows[:,1],np.tile(np.arange(length),count)):
        issues.append('bin_order')
    actual = rows[:,2:].reshape(expected.shape)
    delta = actual - expected
    mismatches = int(np.count_nonzero(delta))
    if mismatches:
        issues.append('integer_codes')
    if status.shape != (count,3):
        issues.append('status_shape')
    elif not np.array_equal(status[:,0],np.arange(count)):
        issues.append('status_order')
    elif not np.array_equal(status[:,2],np.array([int(j['expected_overflow']) for j in jobs])):
        issues.append('overflow')
    return {'pass':not issues,'issues':issues,'transform_count':count,
            'complex_outputs':count*length,'integer_components':count*length*2,
            'mismatched_components':mismatches,'maximum_integer_delta':int(np.max(np.abs(delta))),
            'first_mismatches':np.argwhere(delta != 0)[:20].tolist(),
            'reported_overflow_transforms':int(np.count_nonzero(status[:,2])) if status.shape == (count,3) else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vectors',required=True,type=Path)
    ap.add_argument('--simulation',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit('Refusing to overwrite check result')
    selection = json.loads((a.vectors/'selection.json').read_bytes())
    for name, key in [('inputs.mem','inputs_mem_sha256'),('expected.npy','expected_npy_sha256')]:
        assert hashlib.sha256((a.vectors/name).read_bytes()).hexdigest() == selection[key]
    expected = np.load(a.vectors/'expected.npy',allow_pickle=False)
    def find(name):
        p = a.simulation/name
        return p if p.exists() else a.simulation/(name+'.gz')
    result = compare(table(find('outputs.csv')),expected,table(find('status.csv')),selection['jobs'])
    log = (a.simulation/'simulate.log').read_text(encoding='utf-8',errors='replace')
    if 'PASS FFT29 archive replay: 817 jobs;' not in log or 'Fatal:' in log:
        result['pass'] = False
        result['issues'].append('missing_tb_pass_or_fatal')
    cycles = table(find('cycles.csv'))
    if cycles.shape != (len(selection['jobs']),6) or not np.array_equal(cycles[:,0],np.arange(len(selection['jobs']))):
        result['pass']=False
        result['issues'].append('cycles_shape_or_order')
    else:
        regular = cycles[:-1]
        timing = {}
        for label,left,right in [('config_to_last_output',1,5),('first_input_to_first_output',2,4),
                                 ('first_input_to_last_output',2,5),('last_input_to_first_output',3,4)]:
            v = regular[:,right] - regular[:,left]
            timing[label]={'min':int(v.min()),'max':int(v.max())}
        intervals = np.diff(regular[:,1])
        timing['config_start_interval_including_tb_gap']={'min':int(intervals.min()),'max':int(intervals.max())}
        timing['six_fft_config_start_to_final_output_cycles'] = int((regular[5,5]-regular[0,1]))
        timing['six_fft_reserved_service_cycles'] = int(6*intervals.max())
        timing['single_transform_ms_at_100MHz'] = float(timing['config_to_last_output']['max']/100000)
        timing['six_fft_reserved_ms_at_100MHz'] = float(6*intervals.max()/100000)
        timing['sustained_transforms_per_second_under_tb_schedule'] = float(1e8/intervals.max())
        timing['backpressure_job_cycles'] = cycles[-1].tolist()
        result['timing'] = timing
    result.update({'status':'PASS_SELECTED_FFT29_RTL_ONLY' if result['pass'] else 'FAIL',
                   'source_commit':selection['source_commit'],
                   'covered_case_ids':selection['selected_cases'],
                   'not_covered_case_ids':selection['unselected_cases'],
                   'unique_archived_fft_count':selection['unique_transforms'],
                   'extra_backpressure_repeats':1,'adapter_RTL_tested':False,
                   'IFFT29_tested':False,'full_chain_tested':False})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
