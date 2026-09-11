"""Compare AMD's installed bit-accurate model with pinned A XSim codes.

No AMD binaries are distributed. Model ABI normalization is Q1.24 even
though the application's interpretation of the same signed codes is S25F23.
"""
import argparse
import ctypes as C
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
A = ROOT / 'task-packages/PKG-A-ACQ/tasks/fft-ip-budget-01'
N = 1024

class Generics(C.Structure):
    _fields_ = [(name, C.c_int) for name in ('C_NFFT_MAX', 'C_ARCH', 'C_HAS_NFFT',
        'C_USE_FLT_PT', 'C_INPUT_WIDTH', 'C_TWIDDLE_WIDTH', 'C_HAS_SCALING',
        'C_HAS_BFP', 'C_HAS_ROUNDING', 'C_NSSR', 'C_SYSTOLICFFT_INV')]

class Inputs(C.Structure):
    _fields_ = [('nfft', C.c_int), ('xn_re', C.POINTER(C.c_double)), ('xn_re_size', C.c_int),
        ('xn_im', C.POINTER(C.c_double)), ('xn_im_size', C.c_int),
        ('scaling_sch', C.POINTER(C.c_int)), ('scaling_sch_size', C.c_int), ('direction', C.c_int)]

class Outputs(C.Structure):
    _fields_ = [('xk_re', C.POINTER(C.c_double)), ('xk_re_size', C.c_int),
        ('xk_im', C.POINTER(C.c_double)), ('xk_im_size', C.c_int),
        ('blk_exp', C.c_int), ('overflow', C.c_int)]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def signed25(code):
    code &= (1 << 25) - 1
    return code - (1 << 25) if code & (1 << 24) else code

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dll', type=Path, required=True)
    parser.add_argument('--dependency-dir', type=Path, action='append', default=[])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((A / 'hashes.json').read_text())
    for name, expected in manifest.items():
        assert sha(A / name) == expected, name
    contract = json.loads((A / 'contract.json').read_text())
    required = dict(length=1024, input_component_bits=25, output_component_bits=25,
        application_fraction_bits=23, phase_factor_bits=24, architecture='radix_2_burst_io',
        rounding_ip_option='convergent_rounding', forward_config_hex='0x0AAAAB',
        inverse_config_hex='0x0AAAAA', fft_stage_right_shifts=[1]*10, ifft_stage_right_shifts=[1]*10)
    for name, value in required.items():
        assert contract[name] == value, ('unsupported contract', name)
    # Retain the DLL search handle for the full model lifetime.
    dll_directory = os.add_dll_directory(str(args.dll.resolve().parent))
    dependency_handles = [os.add_dll_directory(str(path.resolve())) for path in args.dependency_dir]
    dll = C.CDLL(str(args.dll.resolve()))
    prefix = 'xilinx_ip_xfft_v9_1_'
    create = getattr(dll, prefix + 'create_state')
    create.argtypes, create.restype = [Generics], C.c_void_p
    simulate = getattr(dll, prefix + 'bitacc_simulate')
    simulate.argtypes, simulate.restype = [C.c_void_p, Inputs, C.POINTER(Outputs)], C.c_int
    destroy = getattr(dll, prefix + 'destroy_state')
    destroy.argtypes, destroy.restype = [C.c_void_p], None
    generics = Generics(10, 2, 0, 0, 25, 24, 1, 0, 1, 1, 0)
    state = create(generics)
    assert state, 'model state allocation failed'
    words = [int(line, 16) for line in (A / 'evidence/run01/inputs.mem').read_text().splitlines()]
    reference = [tuple(map(int, row)) for row in csv.reader((A / 'evidence/run01/outputs.csv').open())]
    assert len(words) == len(reference) == 22 * N
    differences, flags, rows = [], [], []
    try:
        for job in range(22):
            block = words[job*N:(job+1)*N]
            real = (C.c_double*N)(*[signed25(word) / 2**24 for word in block])
            imag = (C.c_double*N)(*[signed25(word >> 32) / 2**24 for word in block])
            shifts = (C.c_int*10)(*([1]*10))
            re_out, im_out = (C.c_double*N)(), (C.c_double*N)()
            inputs = Inputs(10, real, N, imag, N, shifts, 10, int(job < 6))
            outputs = Outputs(re_out, N, im_out, N, 0, 0)
            assert simulate(state, inputs, C.byref(outputs)) == 0, job
            assert outputs.xk_re_size == outputs.xk_im_size == N
            flags.append(outputs.overflow)
            for index in range(N):
                r, i = re_out[index] * 2**24, im_out[index] * 2**24
                assert r.is_integer() and i.is_integer(), (job, index, 'noninteger model code')
                actual = (job, index, int(r), int(i))
                expected = reference[job*N+index]
                assert expected[:2] == (job, index), 'reference ordering'
                rows.append(actual)
                if actual != expected:
                    differences.append(dict(job=job, index=index, actual=list(actual[2:]), expected=list(expected[2:])))
    finally:
        destroy(state)
        dll_directory.close()
        for handle in dependency_handles:
            handle.close()
    with (args.out / 'model-outputs.csv').open('w', newline='') as handle:
        csv.writer(handle, lineterminator='\n').writerows(rows)
    report = dict(status='PASS_PINNED_VECTORS_BIT_EXACT' if not differences and not any(flags) else 'FAIL',
        A_commit='ac0ff38e954dac094fd84e28b329dcb24dded7fb', jobs=22, complex_outputs=len(rows),
        compared_components=2*len(rows), mismatch_complex_samples=len(differences), overflow_flags=flags,
        first_mismatches=differences[:20], model_dll=str(args.dll.resolve()), model_dll_sha256=sha(args.dll),
        header_sha256=sha(args.dll.parent/'xfft_v9_1_bitacc_cmodel.h'),
        generics={name: getattr(generics, name) for name, _ in Generics._fields_},
        model_normalization_fraction_bits=24, application_fraction_bits=23,
        sources={name: sha(A / name) for name in ('hashes.json','contract.json','evidence/run01/inputs.mem','evidence/run01/outputs.csv')},
        runner_sha256=sha(Path(__file__)),
        dependency_dll_hashes={str(p.resolve()): sha(p) for directory in args.dependency_dir for p in directory.glob('*.dll')},
        python=sys.version, platform=platform.platform(),
        output_file_bytes_equal=sha(args.out/'model-outputs.csv') == sha(A/'evidence/run01/outputs.csv'),
        limitation='Archived RTL vs current installed model on 22 pinned vectors only; not new RTL simulation, heldout vectors, full PHAT or hardware acceptance.')
    (args.out/'comparison.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'].startswith('PASS') else 1

if __name__ == '__main__':
    raise SystemExit(main())
