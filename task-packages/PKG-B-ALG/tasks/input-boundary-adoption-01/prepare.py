"""Evaluate the unfrozen B proposal using bundled historical budget sources."""
import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / 'sources.json').read_text(encoding='utf-8'))
    for name, record in manifest.items():
        assert digest(HERE / name) == record['sha256'], name
    config = json.loads((HERE / 'contract.json').read_text(encoding='utf-8'))
    assert config['confirmed_boundary']['h1']['normalization_denominator'] == 2**23
    assert config['confirmed_boundary']['h1']['container_bits'] == 32
    assert config['known']['channels'] == 6
    assert config['pending_A']['processing_clock_hz'] is None
    assert config['pending_A']['input_pcm_effective_bits'] is None
    assert config['pending_A']['least_squares_pl_ps_partition'] == 'PL_TARGET_CONFIRMED_IMPLEMENTATION_PENDING'
    module_path = HERE / 'source-snapshot/fixed-point-contract-01/evaluate_contract.py'
    spec = importlib.util.spec_from_file_location('b_boundary_budget_snapshot', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.evaluate(config)
    assert result['cycles_available_per_hop'] is None
    assert result['serial_fft_ifft_cycles'] is None
    assert result['selected_candidate'] is None
    assert [x['partial_totals']['bit_packed_bytes'] for x in result['candidates']] == [84551, 75317]
    result['confirmed_boundary'] = config['confirmed_boundary']
    result['configured_clock_scenario'] = {
        'clock_hz': 100000000, 'cycles_per_hop': 100000000 * 512 / 48000,
        'status': 'BD_CONFIGURATION_SCENARIO_NOT_MEASURED_TIMING'}
    result['environment'] = dict(python=sys.version, platform=platform.platform())
    result['source_sha256'] = {name: record['sha256'] for name, record in manifest.items()}
    result['source_sha256']['prepare.py'] = digest(Path(__file__))
    result['source_sha256']['contract.json'] = digest(HERE / 'contract.json')
    output = HERE / args.out
    output.mkdir(parents=True, exist_ok=False)
    (output / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    message = 'PASS: source hashes, separated input profiles, PL target, candidate ranges/storage; actual cycles unresolved; no fixed-point or hardware acceptance.'
    (output / 'validation.txt').write_text(message + '\n', encoding='utf-8', newline='\n')
    print(message)

if __name__ == '__main__':
    main()
