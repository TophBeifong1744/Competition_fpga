"""Read-only raw/UART/CSV cross-check; never overwrites captures or old evidence."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import numpy as np


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(path):
    files = {n: (path/n).read_bytes() for n in
             ('raw.bin', 'serial.log', 'metadata.json', 'samples.csv')}
    raw = files['raw.bin']
    meta = json.loads(files['metadata.json'].decode('utf-8-sig'))
    log = files['serial.log'].decode('utf-8-sig')
    require(len(raw) == 1024000, 'raw length')
    records = list(struct.iter_unpack('<IIiiiiII', raw))
    ids = [(v[1] << 32) | v[0] for v in records]
    pcm = np.array([v[2:6] for v in records], dtype=np.int32)
    flags = np.array([v[6] for v in records], dtype=np.uint32)
    require(len(records) == meta['sample_count'] == 32000, 'group count')
    require(ids[0] == meta['first_id'] and ids[-1] == meta['last_id'], 'metadata IDs')
    require(all(v == ids[0]+i for i, v in enumerate(ids)), 'raw discontinuity')
    require(all(v[7] == 0 and v[6] & ~15 == 0 for v in records), 'raw flags/reserved')
    require(bool(np.all((pcm >= -8388608) & (pcm <= 8388607))), 'signed24 range')
    require(sha(raw) == meta['raw_sha256'], 'raw SHA')
    require(sha(files['samples.csv']) == meta['samples_sha256'], 'CSV SHA')
    require(meta['coordinates_m'] is None and meta['source_kind'] == 'hardware-audio'
            and meta['evidence_level'] == 'diagnostic', 'evidence boundary')
    require(meta['acquisition_id'] == path.name, 'acquisition ID')
    require('Dupont wires, no adapter PCB' in meta['source_provenance'], 'physical source')
    require('FOUR_CAPTURE_FAIL' not in log and log.count('FOUR_CAPTURE_INTEGRITY_PASS') == 1,
            'failed/mixed capture log')
    builds = re.findall(r'FOUR PDM capture (\S+) build ([^\r\n]+)', log)
    require(builds == [(meta['config_version'], 'Sep 11 2026 18:23:59')], 'build/config header')
    packets = re.findall(r'DONE packet=(\d+) actual_bytes=(\d+) DMA_SR=([\da-fA-F]{8})', log)
    require(len(packets) == 128, 'packet count')
    require(all(int(p) == i and int(n) == 8000 and int(s,16) == 0x1002
                for i,(p,n,s) in enumerate(packets)), 'packet number/length/status')
    summary = re.findall(r'FOUR_CAPTURE_INTEGRITY_PASS groups=(\d+) bytes=(\d+) packets=(\d+) clip_groups=(\d+)', log)
    require(summary == [('32000','1024000','128', str(int(np.count_nonzero(flags))))], 'UART counts')
    endpoints = re.findall(r'first_id_hex=([\da-fA-F]{16}) last_id_hex=([\da-fA-F]{16})', log)
    require(len(endpoints) == 1 and [int(v,16) for v in endpoints[0]] == [ids[0],ids[-1]], 'UART IDs')
    final = re.findall(r'DMA_SR=([\da-fA-F]{8}) SOURCE_STATUS=([\da-fA-F]{8}) sync_error=(\d+) overflow=(\d+) fnv1a32=([\da-fA-F]{8})', log)
    require(len(final) == 1 and final[0][:4] == ('00001002','0000000A','0','0'), 'final status')
    digest = 2166136261
    for byte in raw:
        digest = ((digest ^ byte)*16777619) & 0xffffffff
    require(digest == int(final[0][4],16), 'UART/raw FNV-1a mismatch')
    require('READY_FOR_DDR_DUMP base=01000000 bytes=1024000 words=256000' in log, 'dump marker')
    rows = list(csv.reader(io.StringIO(files['samples.csv'].decode('utf-8-sig'))))
    require(rows[0] == ['sample_id','mic0','mic1','mic2','mic3','stream_error','error_flags'], 'H1 header')
    require(len(rows) == 32001, 'CSV row count')
    for i,row in enumerate(rows[1:]):
        expected = [str(ids[i]), *map(str, records[i][2:6]), str(int(bool(flags[i]))),
                    'unknown' if flags[i] else '']
        require(row == expected, f'raw/CSV difference at row {i}')
    lane_log = re.findall(r'mic(\d) min=(-?\d+) max=(-?\d+) zeros=(\d+) clipped=(\d+)', log)
    lanes = []
    require(len(lane_log) == 4, 'UART lane count')
    for ch in range(4):
        values = pcm[:,ch].astype(np.float64)
        row = {'channel':ch, 'min':int(values.min()), 'max':int(values.max()),
               'zeros':int(np.count_nonzero(values == 0)),
               'clipped_flags':int(np.count_nonzero(flags & (1 << ch))),
               'mean':float(values.mean()), 'rms_ac_codes':float(values.std()),
               'constant':bool(np.ptp(values) == 0)}
        require(tuple(map(int,lane_log[ch])) == (ch,row['min'],row['max'],row['zeros'],row['clipped_flags']),
                f'UART lane {ch} statistics')
        lanes.append(row)
    require(not np.any(flags), 'reported clipping needs explicit review')
    return {'acquisition_id':path.name, 'groups':len(records), 'bytes':len(raw),
            'duration_configured_seconds':len(records)/meta['sample_rate_hz'],
            'first_id':ids[0], 'last_id':ids[-1], 'build':builds[0][1],
            'fnv1a32':f'{digest:08X}', 'raw_csv_exact_values':True,
            'continuous_within_capture':True, 'error_rows':0, 'packet_count':128,
            'raw_file_sha256':{n:sha(v) for n,v in files.items()}, 'lanes':lanes,
            'identical_lane_pairs':[[a,b] for a in range(4) for b in range(a+1,4)
                                    if np.array_equal(pcm[:,a],pcm[:,b])],
            'scope':'diagnostic file integrity only; not measured synchronization or acoustic acceptance'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--captures', type=Path, required=True)
    p.add_argument('--reader', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    captures = [a.captures/n for n in ('dupont-quiet-01','dupont-speech-01')]
    result = {'status':'RUNNING', 'python':sys.version, 'numpy':np.__version__}
    try:
        result['segments'] = [audit(path) for path in captures]
        command = [sys.executable,'-B',str(a.reader),*map(str,captures)]
        run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        (a.output/'reader.stdout.json').write_text(run.stdout, encoding='utf-8')
        (a.output/'reader.stderr.txt').write_text(run.stderr, encoding='utf-8')
        result['reader_command'] = command
        result['reader_sha256'] = sha(a.reader.read_bytes())
        result['review_script_sha256'] = sha(Path(__file__).read_bytes())
        require(run.returncode == 0, 'reader exit code')
        reader = json.loads(run.stdout)
        require(reader['status'] == 'PASS_FORMAT_ONLY', 'reader result')
        original = json.loads((a.captures/'dupont-reader-check-01.log').read_text(encoding='utf-8-sig'))
        require(reader == original, 'reader differs semantically from submitted log')
        result['reader_matches_original_json'] = True
        result['submitted_reader_log_sha256'] = sha((a.captures/'dupont-reader-check-01.log').read_bytes())
        result['status'] = 'PASS_DIAGNOSTIC_INTEGRITY_NOT_B_REVIEW'
        # Guard against an external task changing inputs while this review was running.
        for capture, segment in zip(captures,result['segments']):
            require(all(sha((capture/n).read_bytes()) == h for n,h in segment['raw_file_sha256'].items()),
                    'input changed during review')
    except Exception as error:
        result['status'] = 'FAIL'
        result['error'] = repr(error)
        raise
    finally:
        (a.output/'integrity.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'])
    for segment in result['segments']:
        print(segment['acquisition_id'], segment['groups'], segment['fnv1a32'],
              'AC RMS:', [round(v['rms_ac_codes'],2) for v in segment['lanes']])


if __name__ == '__main__':
    main()
