"""Four-channel record v1 to H1 0.3; no filtering, resampling or invented channels."""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path

RECORD = struct.Struct('<IIiiiiII')
HEADER = ['sample_id', 'mic0', 'mic1', 'mic2', 'mic3', 'stream_error', 'error_flags']


def decode(raw):
    if not raw or len(raw) % RECORD.size:
        raise ValueError('empty/truncated record stream; original must be retained')
    rows, previous = [], None
    for lo, hi, *values in RECORD.iter_unpack(raw):
        pcm, flags, reserved = values[:4], values[4], values[5]
        sample_id = (hi << 32) | lo
        if reserved or flags & ~15:
            raise ValueError('unsupported flags/reserved word')
        if any(not -(1 << 23) <= v < (1 << 23) for v in pcm):
            raise ValueError('invalid signed24 sign extension')
        if previous is not None and sample_id <= previous:
            raise ValueError('duplicate/backwards/wrapped ID')
        errors = []
        if previous is not None and sample_id != previous + 1:
            errors.append('drop')
        if flags:
            errors.append('unknown')  # H1 has no saturation enum; raw bitmap preserved.
        rows.append([sample_id, *pcm, int(bool(errors)), ';'.join(errors)])
        previous = sample_id
    return rows


def export(raw_path, output, *, acquisition_id, config_version, source_kind,
           provenance, capture_point, sample_rate_hz=48000):
    raw_path, output = Path(raw_path), Path(output)
    if source_kind not in ('synthetic-code', 'hardware-test-pattern', 'hardware-audio'):
        raise ValueError('unsupported source label')
    if not all(isinstance(v, str) and v.strip() for v in
               (acquisition_id, config_version, provenance, capture_point)):
        raise ValueError('explicit identity and provenance required')
    if sample_rate_hz != 48000:
        raise ValueError('this candidate implements configured 48000 Hz only')
    if output.exists():
        raise FileExistsError('preserve earlier export: select new output directory')
    raw = raw_path.read_bytes()
    rows = decode(raw)
    meta = {
        'schema_version': 'ss-data-draft-0.3', 'acquisition_id': acquisition_id,
        'config_version': config_version, 'channel_order': HEADER[1:5],
        'coordinates_m': None, 'geometry_version': 'four-physical-unmeasured-v1',
        'coordinate_system': 'x-forward_y-left_z-up',
        'direction_convention': 'array-to-source', 'angle_unit': 'deg',
        'sample_rate_hz': sample_rate_hz,
        'sample_format': {'encoding': 'signed-pcm', 'storage_dtype': 'int32',
                          'valid_bits': 24, 'alignment': 'right', 'fractional_bits': 0},
        'source_kind': source_kind,
        'evidence_level': 'synthetic' if source_kind == 'synthetic-code' else 'diagnostic',
        'capture_point': capture_point,
        'provisional_fields': {
            'coordinates_m': 'Not measured: no direction calculation permitted.',
            'channel_order': 'Logical lane order only; actual module-to-lane mapping requires recording notes.',
            'sample_rate_hz': 'Configured frequency, not instrument-measured.',
            'sample_format': '24-bit exchange range, not measured effective precision.'},
        'calibration_status': 'not-calibrated', 'source_provenance': provenance,
        'raw_file': 'raw.bin', 'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'raw_layout': 'ss-four-record-0.1: little-endian id_lo,id_hi,mic0..3,flags,reserved; 32 bytes',
        'raw_flags': 'bits0..3 per-lane saturation -> H1 unknown; other bits unsupported; raw.bin retained',
        'sample_count': len(rows), 'first_id': rows[0][0], 'last_id': rows[-1][0],
        'processing': 'none; preserve raw IDs/PCM; do not fill gaps or concatenate acquisitions',
        'limits': 'Caller source declaration is not verified acoustically by this converter; no H2/M1 approval.'}
    output.mkdir(parents=True)
    (output / 'raw.bin').write_bytes(raw)
    with (output / 'samples.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(HEADER)
        writer.writerows(rows)
    meta['samples_sha256'] = hashlib.sha256((output / 'samples.csv').read_bytes()).hexdigest()
    (output / 'metadata.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('output', type=Path)
    for name in ('acquisition-id', 'config-version', 'source-kind', 'provenance', 'capture-point'):
        parser.add_argument('--'+name, required=True)
    args = vars(parser.parse_args())
    args['raw_path'] = args.pop('raw')
    result = export(**args)
    print('EXPORT_PASS', result['sample_count'], result['raw_sha256'])
