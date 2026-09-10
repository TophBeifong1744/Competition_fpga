"""Portable, stdlib-only export/verification of TWO explicitly sourced captures.

Reuses the original decoder's <IIiI / FNV / signed24 / ID validation rules.
No blanket hardware source claim; this is not a generic hardware authenticator.
"""
import argparse
import csv
import hashlib
import io
import json
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'originals/mono_acceptance_20260910'
RECORDS = {
    'quiet_03': ('72c4dacb70618d0cae19c634db22d569782286f32131af2bdeb56c1a1f535c5a', 'EFFF882A', 14223, 62222, -23616, 26176, 168),
    'music_04': ('cd1345f14c8ad18f9f555eded2aa07c4d81193bd14965738306c7d451405c17f', 'C7762DD9', 13352, 61351, -18816, 28288, 176),
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def decode(raw, expected_fnv):
    require(len(raw) == 768000, 'Expected 48000 records / 768000 bytes')
    h = 2166136261
    for value in raw:
        h = ((h ^ value) * 16777619) & 0xffffffff
    require(f'{h:08X}' == expected_fnv.upper(), 'FNV mismatch')
    rows = []
    for lo, hi, pcm, flags in struct.iter_unpack('<IIiI', raw):
        sid = (hi << 32) | lo
        require(-8388608 <= pcm <= 8388607, 'Not sign-extended signed24')
        require(flags & ~2 == 0, 'Error/unknown flags: retain raw, refuse clean export')
        require(not rows or sid == rows[-1][0] + 1, 'Discontinuous original ID')
        rows.append((sid, pcm, flags))
    return rows

def build(label):
    expected_sha, fnv, first, last, minimum, maximum, zeros = RECORDS[label]
    raw_path = ORIGINAL / 'quiet_music' / (label + '.bin')
    raw = raw_path.read_bytes()
    require(sha(raw) == expected_sha, 'Source SHA mismatch: ' + label)
    rows = decode(raw, fnv)
    require((rows[0][0], rows[-1][0]) == (first, last), 'Serial ID mismatch')
    require((min(r[1] for r in rows), max(r[1] for r in rows), sum(r[1] == 0 for r in rows)) == (minimum, maximum, zeros), 'Serial statistics mismatch')
    require(all(r[2] == 0 for r in rows), 'These archived captures report zero flags')
    require(all(r[1] % 32 == 0 for r in rows), 'CIC scaling inconsistent')
    wav_path = raw_path.with_name(label + '_original24.wav')
    with wave.open(str(wav_path), 'rb') as wav:
        require((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (1, 3, 48000, 48000), 'WAV header mismatch')
        wav_bytes = wav.readframes(48000)
    require(wav_bytes == b''.join((r[1] & 0xffffff).to_bytes(3, 'little') for r in rows), 'WAV sample mismatch')
    text = io.StringIO(newline='')
    writer = csv.writer(text, lineterminator='\n')
    writer.writerow(['sample_id', 'pcm', 'flags'])
    writer.writerows(rows)
    csv_bytes = text.getvalue().encode('utf-8')
    snapshot = ORIGINAL / 'snapshot'
    metadata = {
        'schema_version': 'ss-mono-diagnostic-0.2',
        'acquisition_id': label + '-' + expected_sha[:16],
        'source_kind': 'user-reported-hardware-audio',
        'evidence_level': 'diagnostic',
        'source_provenance': {
            'description': 'User-labelled quiet/music capture, matched to user-pasted serial transcript; not independently observed on site.',
            'recording_date': '2026-09-10', 'recording_time': None,
            'serial_log_kind': 'user-pasted transcript, Markdown escaping normalized',
            'serial_log': '../../originals/mono_acceptance_20260910/serial-user-transcript.txt',
            'serial_log_sha256': sha((ORIGINAL / 'serial-user-transcript.txt').read_bytes()),
            'condition_label': label, 'fixed_position': 'user-reported; unmeasured',
            'latest_listening': 'A relayed user report: song fairly clear, no obvious hum, interruptions or distortion; subjective, not instrument evidence.',
            'capture_restart_relation': 'unknown; recordings are separate intervals, do not concatenate IDs',
        },
        'raw_file': '../../originals/mono_acceptance_20260910/quiet_music/' + label + '.bin',
        'raw_sha256': expected_sha, 'raw_bytes': len(raw), 'fnv1a32': fnv,
        'samples_sha256': sha(csv_bytes),
        'channel_count': 1, 'channel_order': ['mic0'],
        'channel_mapping_status': 'logical single input; physical module serial number unknown',
        'sample_rate_hz': 48000, 'sample_rate_status': 'configured, not measured',
        'measured_sample_rate_hz': None, 'nominal_duration_s': 1,
        'pdm_clock_hz_configured': 3072000, 'pl_clock_hz_configured': 61440000,
        'sample_format': {'storage_dtype': 'int32', 'encoding': 'signed-pcm', 'code_bits': 24, 'measured_effective_bits': None, 'fractional_bits': 0},
        'scaling': 'PDM 0=-1 / 1=+1; CIC3 R64 M1 gain 262144; multiply by 32 then signed24 saturation; divide PCM by 8388608 only for dimensionless full-scale normalization, not pascals.',
        'processing_applied_to_csv': 'none; no DC removal, gain, filtering or renumbering',
        'filter_compensation': 'none; CIC passband droop and alias rejection limitations remain',
        'warmup_discard_samples_configured': 4096,
        'id_origin': 'PCM outputs since frontend reset, including warmup/idle outputs',
        'sample_count': len(rows), 'first_id': first, 'last_id': last,
        'continuous_intervals': [{'first_id': first, 'last_id': last, 'sample_count': len(rows)}],
        'flags_encoding': {'bit0': 'reserved overflow; rejected by this clean-capture reader', 'bit1': 'PCM saturation', 'bits2_31': 'unknown/reserved; rejected'},
        'observed_errors': {'id_gaps': 0, 'nonzero_flags': 0, 'clipped_samples': 0, 'reported_source_status_hex': '0000000A', 'reported_dma_status_hex': '00001002', 'unobserved_errors_excluded': False},
        'microphone_positions_m': None, 'source_azimuth_deg': None, 'source_elevation_deg': None, 'source_distance_m': None,
        'calibration': 'not measured / not calibrated',
        'capture_point': 'reported PS DDR after DMA S2MM and cache invalidation, then post-capture JTAG dump',
        'raw_layout': 'little endian: uint32 ID low, uint32 ID high, int32 PCM, uint32 flags; 16 bytes/record',
        'configuration_version': 'mono-capture-v1; serial build Sep 10 2026 14:48:35; snapshot-associated, not load-bound',
        'post_capture_snapshot_sha256': {name: sha((snapshot / name).read_bytes()) for name in ['pdm_cic3.v', 'pcm_capture_axis.v', 'single_mic_top.v', 'main_mono_capture.c', 'system_single_mic.bit', 'system_single_mic.xsa', 'single_mic_capture.elf']},
        'loaded_identity_verified': False,
        'limitations': ['Single channel only; not four-channel ss-data-draft-0.3 and not six-mic DOA input.', 'Full four-channel H2 remains missing.', 'VCCO/VDD, external CLOCK/DATA timing, actual clock and load identity are not verified.', 'Low-frequency bias/decay cause remains unresolved; no SNR, precision or final audio quality claim.'],
        'acoustic_acceptance': False,
    }
    return csv_bytes, metadata

def export(destination):
    require(not destination.exists(), 'Refuse overwrite: ' + str(destination))
    built = {label: build(label) for label in RECORDS}
    for label, (csv_bytes, metadata) in built.items():
        folder = destination / label
        folder.mkdir(parents=True)
        (folder / 'samples.csv').write_bytes(csv_bytes)
        (folder / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def verify(destination):
    results = []
    for label in RECORDS:
        expected_csv, expected_meta = build(label)
        folder = destination / label
        require((folder / 'samples.csv').read_bytes() == expected_csv, 'CSV differs from raw: ' + label)
        require(json.loads((folder / 'metadata.json').read_text(encoding='utf-8')) == expected_meta, 'Metadata mismatch: ' + label)
        results.append({'recording': label, 'result': 'PASS', 'samples': 48000, 'raw_sha256': expected_meta['raw_sha256'], 'fnv1a32': expected_meta['fnv1a32'], 'first_id': expected_meta['first_id'], 'last_id': expected_meta['last_id']})
    return {'result': 'PASS', 'scope': 'offline export integrity, not board acceptance', 'records': results}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['export', 'verify'])
    parser.add_argument('--directory', type=Path, default=ROOT / 'data')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.command == 'export':
        export(args.directory)
    result = verify(args.directory)
    if args.report:
        require(not args.report.exists(), 'Refuse report overwrite')
        args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
