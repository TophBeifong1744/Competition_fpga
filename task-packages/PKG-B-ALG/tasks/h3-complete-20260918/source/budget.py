"""Recalculate four-channel H3 operation, storage and transfer bounds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def calculate():
    fs, n, hop, pairs, bins = 48000, 1024, 512, 6, 513
    hop_cycles_100m = 100_000_000 * hop // fs
    forward_slot, inverse_slot = 7366, 7406
    fft_service = 4 * forward_slot + 6 * inverse_slot
    buffers = {
        "pcm_double_frame_int32": 4 * n * 4 * 2,
        "hann_u18_slot32": n * 4,
        "four_half_spectra_complex_slot32": 4 * bins * 2 * 4,
        "one_pair_phat_complex_slot32": bins * 2 * 4,
        "one_pair_ifft_full_complex_slot32": n * 2 * 4,
        "one_pair_real_correlation_int32": n * 4,
        "audio_history_four_channels_int32": 4 * 10 * 4,
        "mono_output_hop_double_buffer_int32": hop * 4 * 2,
        "current_h1_dma_two_slots_with_guards": 2 * (8000 + 64),
        "exponent_status_descriptor_allowance": 1024
    }
    return {
        "status": "CALCULATED_AND_EVIDENCE_GRADED_NOT_REALTIME_PASS",
        "frame": {"sample_rate_hz": fs, "length": n, "hop": hop,
                  "frame_ms": n / fs * 1000, "hop_ms": hop / fs * 1000, "frames_per_second": fs / hop},
        "transforms": {"forward_per_frame": 4, "inverse_max_per_frame": 6,
                       "forward_slot_cycles_measured_test_scheduler": forward_slot,
                       "inverse_slot_cycles_measured_test_scheduler": inverse_slot,
                       "service_cycles_sum": fft_service, "service_ms_at_configured_100mhz": fft_service / 100000,
                       "hop_cycles_at_configured_100mhz": hop_cycles_100m,
                       "remaining_before_other_work": hop_cycles_100m - fft_service,
                       "warning": "two historical OOC candidates; not one proven mixed-width integrated scheduler"},
        "operations": {
            "window_multiplies_per_frame": 4 * n,
            "cross_spectrum_bins_per_frame": pairs * bins,
            "cross_real_multiplies_per_frame": pairs * bins * 4,
            "cross_add_sub_per_frame": pairs * bins * 2,
            "maximum_retained_band_bins": pairs * 79,
            "lag_search_points": 4 * 13 + 2 * 17,
            "lag_interpolation_divisions_max": pairs,
            "das_fractional_channel_interpolations_per_hop": 4 * hop,
            "symbolic_other_cycles": "6*513*C_cross + B*(C_sqrt+4*C_newton+2*C_output) + 86*C_compare + 6*C_div + C_DOA + 2048*C_DAS + C_DMA + C_switch + C_stall"
        },
        "buffers_bytes": buffers | {"listed_total_no_lifetime_reuse": sum(buffers.values())},
        "bandwidth_bytes_per_second": {
            "pcm24_net": 4 * fs * 3,
            "pcm_int32_net": 4 * fs * 4,
            "h1_group_transport_32_bytes": fs * 32,
            "overlap_full_window_reads_int32": 4 * n * 4 * (fs / hop),
            "ten_transform_materialize_read_plus_write": 10 * n * 8 * 2 * (fs / hop),
            "mono_int32_output": fs * 4
        },
        "latency": {
            "frame_collection_ms": n / fs * 1000,
            "five_valid_frame_best_case_collection_ms": (n + 4 * hop) / fs * 1000,
            "common_audio_availability_delay_ms": 8 / fs * 1000,
            "fade_ms": 480 / fs * 1000,
            "hold_ms_not_processing_latency": 200,
            "end_to_end_limit_ms": None,
            "actual_integrated_processing_ms": None
        },
        "evidence": {
            "forward_fft29": "OOC XSim/P&R evidence; 7366-cycle test slot; limited research approval",
            "inverse_fft25": "historical OOC XSim/synthesis evidence; 7406-cycle test slot",
            "processing_clock": "configured 100 MHz, not board-measured full-chain clock",
            "phat_lag_doa_das_dma_switch": "formula/estimate only; no integrated cycle measurement",
            "cache_total": "calculated conservative list; not BRAM mapping or proven lifetime optimum"
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(calculate(), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("PASS_BUDGET_RECALCULATION_NOT_REALTIME")


if __name__ == "__main__":
    main()
