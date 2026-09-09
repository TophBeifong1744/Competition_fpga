"""Strict ss-data-draft-0.3 reader. Format validation is not acoustic acceptance."""
from __future__ import annotations
import argparse
import copy
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import numpy as np

SCHEMA = 'ss-data-draft-0.3'
CHANNELS = ['mic0', 'mic1', 'mic2', 'mic3']
HEADER = ['sample_id', *CHANNELS, 'stream_error', 'error_flags']
FORMAT = dict(encoding='signed-pcm', storage_dtype='int32', valid_bits=24,
              alignment='right', fractional_bits=0)
INTEGER = re.compile(r'[+-]?[0-9]+\Z')
FLAGS = {'drop', 'overflow', 'relock', 'unknown'}
CONFIG_FIELDS = ['schema_version', 'channel_order', 'coordinates_m', 'geometry_version',
                 'coordinate_system', 'direction_convention', 'angle_unit', 'sample_rate_hz',
                 'sample_format', 'capture_point', 'provisional_fields', 'calibration_status',
                 'calibration_record']


class DataError(ValueError):
    def __init__(self, code, field, message, line=None):
        self.code, self.field, self.line = code, field, line
        super().__init__(f'{code}: {field}' + (f' at CSV physical line {line}' if line else '') + f': {message}')


def need(condition, code, field, message, line=None):
    if not condition: raise DataError(code, field, message, line)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    if type(value) not in (int, float): return False
    try: return math.isfinite(value)
    except OverflowError: return False


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate_key', key, 'duplicate JSON key')
        result[key] = value
    return result


def bad_constant(value):
    raise DataError('nonfinite_json', 'metadata', f'non-standard JSON constant {value}')


def metadata_from_bytes(raw):
    try:
        meta = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=bad_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise DataError('invalid_json', 'metadata', str(error)) from error
    need(isinstance(meta, dict), 'type', 'metadata', 'expected object')
    required = ['schema_version', 'acquisition_id', 'config_version', 'channel_order',
                'coordinates_m', 'geometry_version', 'coordinate_system', 'direction_convention',
                'angle_unit', 'sample_rate_hz', 'sample_format', 'source_kind', 'evidence_level',
                'capture_point', 'provisional_fields', 'calibration_status']
    for key in required: need(key in meta, 'missing_field', key, 'required metadata field')
    need(meta['schema_version'] == SCHEMA, 'unsupported_schema', 'schema_version', 'expected '+SCHEMA)
    for key in ['acquisition_id', 'config_version', 'geometry_version', 'capture_point']:
        need(text(meta[key]), 'type', key, 'expected nonempty string')
    need(meta['channel_order'] == CHANNELS, 'channel_order', 'channel_order', 'expected unique mic0..mic3 in order')
    for key, value in [('coordinate_system', 'x-forward_y-left_z-up'),
                       ('direction_convention', 'array-to-source'), ('angle_unit', 'deg')]:
        need(meta[key] == value, 'unsupported_value', key, 'expected '+value)
    need(number(meta['sample_rate_hz']) and meta['sample_rate_hz'] > 0,
         'numeric_range', 'sample_rate_hz', 'finite positive number, not bool')
    fmt = meta['sample_format']
    need(isinstance(fmt, dict) and fmt.keys() == FORMAT.keys(), 'sample_format', 'sample_format', 'exact supported format required')
    for key, value in FORMAT.items():
        need(type(fmt[key]) is type(value) and fmt[key] == value, 'sample_format',
             'sample_format.'+key, 'unsupported value or type')
    provisional = meta['provisional_fields']
    need(isinstance(provisional, dict) and all(text(k) and text(v) for k, v in provisional.items()),
         'type', 'provisional_fields', 'expected object of nonempty reasons')
    coords = meta['coordinates_m']
    if coords is None:
        need('coordinates_m' in provisional, 'missing_reason', 'provisional_fields.coordinates_m', 'unknown coordinates need reason')
    else:
        need(isinstance(coords, list) and len(coords) == 4 and all(isinstance(row, list) and len(row) == 3
             and all(number(v) for v in row) for row in coords), 'coordinates', 'coordinates_m', 'finite numeric 4x3 array required')
    if meta['capture_point'] == 'unknown':
        need('capture_point' in provisional, 'missing_reason', 'provisional_fields.capture_point', 'unknown capture point needs reason')
    need(meta['source_kind'] in ['synthetic-code', 'synthetic-acoustic', 'hardware-test-pattern', 'hardware-audio'],
         'source_kind', 'source_kind', 'unsupported source kind')
    need(meta['evidence_level'] in ['synthetic', 'diagnostic', 'accepted'], 'evidence', 'evidence_level', 'unsupported evidence level')
    if meta['source_kind'].startswith('synthetic-'):
        need(meta['evidence_level'] == 'synthetic', 'evidence', 'evidence_level', 'synthetic source must remain synthetic')
    else:
        need(meta['evidence_level'] in ['diagnostic', 'accepted'], 'evidence', 'evidence_level', 'hardware source needs diagnostic or documented accepted')
    need(meta['calibration_status'] in ['not-calibrated', 'partial', 'calibrated'], 'calibration', 'calibration_status', 'unsupported calibration status')
    for condition, key in [(meta['calibration_status'] == 'calibrated', 'calibration_record'),
                           (meta['evidence_level'] == 'accepted', 'acceptance_record')]:
        if condition: need(text(meta.get(key)), 'missing_record', key, 'nonempty reference required; human verification still pending')
    return meta


def integer(token, field, low, high, line):
    need(bool(INTEGER.fullmatch(token)), 'integer_literal', field, 'decimal integer without whitespace required', line)
    try: result = int(token, 10)
    except ValueError as error: raise DataError('integer_range', field, 'integer literal too long', line) from error
    need(low <= result <= high, 'integer_range', field, f'expected {low}..{high}', line)
    return result


@dataclass
class Recording:
    metadata: dict
    sample_ids: np.ndarray
    samples: np.ndarray
    stream_error: np.ndarray
    error_flags: tuple
    clean_intervals: tuple
    missing_intervals: tuple
    file_hashes: dict

    def direction_policy(self):
        if self.metadata['source_kind'] in ['synthetic-code', 'hardware-test-pattern']:
            return 'forbidden_non_acoustic_input'
        if self.metadata['coordinates_m'] is None:
            return 'forbidden_unknown_coordinates'
        # This reader never verifies physical geometry or signs off acceptance.
        return 'diagnostic_only_requires_geometry_and_algorithm_validation'

    def summary(self):
        return dict(schema_version=SCHEMA, acquisition_id=self.metadata['acquisition_id'],
            config_version=self.metadata['config_version'], samples=len(self.sample_ids),
            sample_id_dtype=str(self.sample_ids.dtype), pcm_dtype=str(self.samples.dtype),
            first_sample_id=int(self.sample_ids[0]), last_sample_id=int(self.sample_ids[-1]),
            clean_intervals=list(self.clean_intervals), missing_intervals=list(self.missing_intervals),
            error_rows=int(self.stream_error.sum()), direction_policy=self.direction_policy(),
            declared_evidence=self.metadata['evidence_level'], acceptance_verified=False,
            calibration_verified=False, file_sha256=self.file_hashes,
            amplitude_all_rows=dict(minimum=self.samples.min(axis=0).tolist(), maximum=self.samples.max(axis=0).tolist(),
                mean=self.samples.mean(axis=0).tolist(),
                full_scale_code_count=np.sum((self.samples == -2**23) | (self.samples == 2**23-1), axis=0).tolist()),
            notes=['Amplitude statistics include error rows; full-scale codes alone do not prove clipping.',
                   'Clean intervals are format-clean only, not verified acoustically clean.',
                   'JSON sample IDs are exact decimal integers; JS consumers must use lossless/BigInt parsing.'])


class ReaderSession:
    """Registry across explicitly loaded segments. No merging or resampling."""
    def __init__(self):
        self.configurations, self.geometries, self.acquisition_ends = {}, {}, {}

    def load(self, directory):
        path = Path(directory)
        try:
            meta_raw = (path/'metadata.json').read_bytes()
            csv_raw = (path/'samples.csv').read_bytes()
        except OSError as error: raise DataError('io', 'input', str(error)) from error
        meta = metadata_from_bytes(meta_raw)
        config = {k: copy.deepcopy(meta.get(k)) for k in CONFIG_FIELDS}
        geometry = {k: copy.deepcopy(meta[k]) for k in ['channel_order', 'coordinates_m', 'coordinate_system']}
        cv, gv, av = meta['config_version'], meta['geometry_version'], meta['acquisition_id']
        need(cv not in self.configurations or config == self.configurations[cv], 'config_conflict', 'config_version', 'same version has different configuration')
        need(gv not in self.geometries or geometry == self.geometries[gv], 'geometry_conflict', 'geometry_version', 'same geometry version has different geometry')
        try: lines = csv_raw.decode('utf-8-sig').splitlines()
        except UnicodeError as error: raise DataError('encoding', 'samples.csv', 'expected UTF-8') from error
        need(bool(lines), 'empty_csv', 'samples.csv', 'missing header')
        ids, samples, errors, flags, gaps, clean = [], [], [], [], [], []
        run_start = None
        for lineno, raw in enumerate(lines, 1):
            need(bool(raw), 'empty_row', 'samples.csv', 'empty data line', lineno)
            try: cells = next(csv.reader([raw], strict=True))
            except csv.Error as error: raise DataError('csv_syntax', 'samples.csv', str(error), lineno) from error
            if lineno == 1:
                need(cells == HEADER, 'header', 'header', 'exact column order required', lineno)
                continue
            need(len(cells) == 7, 'columns', 'samples.csv', 'expected seven columns', lineno)
            sample_id = integer(cells[0], 'sample_id', 0, 2**64-1, lineno)
            pcm = [integer(cells[i+1], key, -2**23, 2**23-1, lineno) for i, key in enumerate(CHANNELS)]
            err = integer(cells[5], 'stream_error', 0, 1, lineno)
            tokens = cells[6].split(';') if cells[6] else []
            need(bool(err) == bool(tokens), 'error_inconsistency', 'error_flags', 'error flag and tokens disagree', lineno)
            need(len(tokens) == len(set(tokens)) and all(token in FLAGS for token in tokens),
                 'unsupported_flags', 'error_flags', 'unknown, duplicate or whitespace-containing token', lineno)
            if ids:
                previous = ids[-1]  # Python integer: previous+1 never wraps uint64.
                need(sample_id > previous, 'id_order', 'sample_id', 'duplicate, decreasing or wrapped ID', lineno)
                if sample_id > previous+1:
                    need(err == 1 and 'drop' in tokens, 'silent_gap', 'error_flags', 'missing drop indication', lineno)
                    gaps.append(dict(first=previous+1, last=sample_id-1, count=sample_id-previous-1))
            index = len(ids)
            if err:
                if run_start is not None:
                    clean.append(dict(row_start=run_start, row_stop=index, first_sample_id=ids[run_start], last_sample_id=ids[-1]))
                    run_start = None
            elif run_start is None: run_start = index
            ids.append(sample_id); samples.append(pcm); errors.append(err); flags.append(tuple(tokens))
        need(bool(ids), 'no_samples', 'samples.csv', 'header only is not a recording')
        if run_start is not None:
            clean.append(dict(row_start=run_start, row_stop=len(ids), first_sample_id=ids[run_start], last_sample_id=ids[-1]))
        need(av not in self.acquisition_ends or ids[0] > self.acquisition_ends[av],
             'acquisition_overlap', 'acquisition_id', 'load segments chronologically without overlap; reset needs a new acquisition ID')
        # Commit registry only after the entire recording has passed validation.
        self.configurations[cv] = config; self.geometries[gv] = geometry; self.acquisition_ends[av] = ids[-1]
        return Recording(copy.deepcopy(meta), np.array(ids, dtype=np.uint64), np.array(samples, dtype=np.int32),
            np.array(errors, dtype=np.uint8), tuple(flags), tuple(clean), tuple(gaps),
            {'metadata.json': hashlib.sha256(meta_raw).hexdigest(), 'samples.csv': hashlib.sha256(csv_raw).hexdigest()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    session = ReaderSession()
    try: reports = [session.load(p).summary() for p in args.directories]
    except DataError as error:
        print(json.dumps(dict(status='ERROR', code=error.code, field=error.field, csv_line=error.line, message=str(error)), ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(dict(status='PASS_FORMAT_ONLY', segments=reports), ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__': sys.exit(main())
