"""Arithmetic only: no acoustic simulation, synthesis, timing or board testing."""
import argparse
import csv
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FS, N, H = 48000, 1024, 512

def evaluate(channels, clock_hz):
    if channels not in (4, 6) or clock_hz <= 0:
        raise ValueError('Only explicitly scoped four/six channel arithmetic')
    pairs = channels * (channels - 1) // 2
    transforms = channels + pairs
    hop_cycles = clock_hz * H // FS
    slot = 8000
    reserve = (hop_cycles + 4) // 5  # proposed 20% ceiling reservation
    return {
        'channels': channels, 'pairs': pairs, 'clock_hz_scenario': clock_hz,
        'classification': 'CALCULATED_SCENARIO_NOT_ADMISSION',
        'fft_count': channels, 'ifft_count_max': pairs,
        'cycles_per_hop_floor': hop_cycles,
        'fft_slot_cycles_proposed': slot,
        'fft_service_cycles_proposed': transforms * slot,
        'fft_service_ms_proposed': transforms * slot * 1000 / clock_hz,
        'fft_service_cycles_from_observed_serial_interval': transforms * 7406,
        'non_fft_cycles_before_margin': hop_cycles - transforms * slot,
        'margin_cycles_proposed': reserve,
        'non_fft_cycles_after_proposed_margin': hop_cycles - transforms * slot - reserve,
        'pcm24_payload_Bps': channels * FS * 3,
        'pcm_int32_payload_Bps': channels * FS * 4,
        'full_overlap_frame_reads_int32_Bps': channels * N * 4 * FS // H,
        'illustrative_record_bytes': channels * 4 + 8 + 4,
        'illustrative_record_Bps': (channels * 4 + 12) * FS,
        'transport_warning': '32-bit PCM + uint64 ID + flags32 is illustration only, no frozen four/six DMA packing; CSV sizes are unrelated',
        'buffers_int32_complex32_components_bytes': {
            'input_ring': channels * N * 4,
            'new_hop_pingpong_separate_allocation': 2 * channels * H * 4,
            'retained_half_spectra': channels * (N//2+1) * 2 * 4,
            'one_full_complex_ifft_assembly': N * 2 * 4,
            'one_pair_correlation': N * 4,
            'mono_output_hop_pingpong': 2 * H * 4,
            'eight_sample_history_geometry_dependent': 8 * channels * 4,
        },
        'buffer_warning': 'Inventory, not sum/BRAM allocation; lifetimes, port conflicts, IP RAM, alignment, weights, PHAT/LS/FIFO/CDC missing',
    }

def calculate():
    cycles_path = ROOT / 'references/fft/evidence/run01/cycles.csv'
    with cycles_path.open(encoding='utf-8', newline='') as f:
        times = [list(map(int, row)) for row in csv.reader(f)]
    if len(times) != 22 or [r[0] for r in times] != list(range(22)):
        raise ValueError('FFT archive job count/order mismatch')
    durations = [r[5]-r[1]+1 for r in times[:21]]
    intervals = [times[i+1][1]-times[i][1] for i in range(20)]
    if set(durations) != {7402} or set(intervals) != {7406}:
        raise ValueError('FFT archive interval changed')
    return {
        'classification': 'CALCULATED_FROM_PINNED_INPUTS_NOT_H3_APPROVAL',
        'fs_hz_configured': FS, 'frame_samples': N, 'hop_samples': H,
        'frame_ms': N*1000/FS, 'hop_ms': H*1000/FS, 'frames_per_second': FS/H,
        'initial_five_accepted_frames_best_case_ms': (N+4*H)*1000/FS,
        'tracker_hold_ms_from_existing_B_config': 200,
        'fade_ms_from_B_budget': 480*1000/FS,
        'cic3_R64_group_delay_pdm_samples': float(Fraction(3*(64-1), 2)),
        'cic3_R64_group_delay_pcm_samples': float(Fraction(3*(64-1), 2*64)),
        'cic3_R64_group_delay_us': float(Fraction(3*(64-1)*1000000, 2*3072000)),
        'cic_warning': 'Ideal linear CIC group delay only, excludes pin synchronizer/pipeline/output phase; not measured total acquisition latency',
        'mono_diagnostic': {
            'record_bytes': 16, 'capture_samples': 48000, 'capture_bytes': 768000,
            'packet_samples': 250, 'packet_bytes': 4000, 'packet_fill_ms': 250*1000/FS,
            'fifo_records': 1024, 'fifo_bytes': 16384,
            'fifo_empty_to_full_ms_no_service': 1024*1000/FS,
            'startup_discard_ms': 4096*1000/FS,
            'ddr_reservation_bytes': 0x01100000-0x01000000,
            'tail_guard_bytes': 64, 'payload_and_guard_fit': 768000+64 <= 1048576,
            'binary_capture_rate_Bps': 16*FS,
            'continuous_stream_or_output_proven': False,
        },
        'fft_archive': {
            'evidence_kind': 'CYCLE_COUNTS_RECOMPUTED_FROM_PRIOR_XSIM_LOG_NOT_BOARD',
            'config_to_last_output_inclusive': durations[0],
            'serial_config_interval': intervals[0],
            'first_input_to_first_output': times[0][4]-times[0][2],
            'stressed_job_duration': times[-1][5]-times[-1][1]+1,
            'new_xsim_run': False,
        },
        'scenarios': [evaluate(c, clock) for c in (4,6) for clock in (61440000,100000000)],
        'whole_system_DSP_allocation': None,
        'whole_system_BRAM_allocation': None,
        'end_to_end_audio_latency_limit_ms': None,
        'note': 'No four-channel acoustic simulation or channel-count performance comparison performed.',
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = calculate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print('CALCULATION_PASS: arithmetic scenarios only;', args.out)
