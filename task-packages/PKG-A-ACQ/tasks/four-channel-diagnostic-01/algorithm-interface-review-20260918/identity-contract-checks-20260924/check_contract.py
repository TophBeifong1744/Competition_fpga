"""Finite synthetic D14-02 document probes; NOT a production identity generator.

Requires jsonschema==4.25.1. No external reference resolution, DUT or EDA run.
Run with --validator-deps for an isolated dependency folder, --out for JSON evidence.
"""
import argparse
import copy
import hashlib
import importlib.metadata
import json
from math import gcd
from pathlib import Path
import sys


def fail(message):
    raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            fail('duplicate decoded key')
        result[key] = value
    return result


def encode(value):
    if isinstance(value, str):
        parts = []
        for char in value:
            code = ord(char)
            if code > 127:
                fail('non-ASCII')
            if char in ('"', '\\'):
                parts.append('\\' + char)
            elif code < 32 or code == 127:
                parts.append('\\u%04x' % code)
            else:
                parts.append(char)
        return '"' + ''.join(parts) + '"'
    if isinstance(value, list):
        return '[' + ','.join(encode(item) for item in value) + ']'
    if isinstance(value, dict):
        return '{' + ','.join(encode(k) + ':' + encode(value[k]) for k in sorted(value)) + '}'
    fail('non-string scalar')


def canonical(raw):
    if raw.startswith(b'\xef\xbb\xbf'):
        fail('BOM')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                       parse_constant=lambda _: fail('non-JSON constant'))
    return encode(value).encode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validator-deps', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.validator_deps:
        sys.path.insert(0, str(args.validator_deps.resolve()))
    from jsonschema import Draft202012Validator
    version = importlib.metadata.version('jsonschema')
    if version != '4.25.1':
        fail('expected jsonschema 4.25.1')
    schema_path = Path(__file__).resolve().parent.parent / 'identity-container-v1.schema.json'
    schema_bytes = schema_path.read_bytes()
    schema = json.loads(schema_bytes)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
        if not condition:
            fail(name)

    def rejected(name, action):
        try:
            action()
        except ValueError:
            check(name, True)
        else:
            check(name, False)

    def ref(name):
        return dict(schema_id='ss-' + name + '-v1', schema_version='1',
                    schema_sha256='a' * 64, encoding='ss-canonical-json-v1',
                    content_sha256='b' * 64)

    def rational(n, d='1'):
        return dict(numerator=str(n), denominator=d)

    common = dict(schema='ss-identity-container-v1', version='1')
    geometry = dict(common, kind='geometry', scope='four-mic-planar-design',
                    coordinate_unit='mm', speed_unit='mm-per-second', reference_mic='mic0',
                    x_axis='mic0-to-mic1', y_axis='mic0-to-mic3',
                    angle_convention='atan2-y-x-degrees', speed_of_sound=rational(343000),
                    mics=[dict(channel=str(i), mic_id='mic' + str(i),
                               x=rational(x), y=rational(y), z=rational(0))
                          for i, (x, y) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])])
    numeric = dict(common, kind='numeric', profile_id='synthetic-only',
                   geometry_sha256='c' * 64, twiddle_backend='portable-q30',
                   algorithm_ref=ref('numeric-algorithm'), source_manifest_ref=ref('numeric-source-manifest'))
    config = dict(common, kind='config', geometry_sha256='c' * 64, numeric_sha256='d' * 64,
                  acquisition=dict(sample_rate_hz='48000', frame_length='1024', hop='512',
                                   channels='4', row_words='8', format='h1-0.3-s24-signext-le32',
                                   capture_contract_ref=ref('capture-contract')),
                  transport=dict(worker='single-owner', isr='enqueue-only',
                                 rx_release='after-successful-copy', token='session-generation-slot',
                                 session='boot-scoped-monotone-u64', generation='object-lifetime-monotone-u64',
                                 binding_ref=ref('transport-binding')),
                  **{name.replace('-', '_') + '_ref': ref(name)
                     for name in ['activity', 'calibration', 'tracker', 'ttl', 'required-units', 'timebase']})
    fixtures = [geometry, numeric, config]
    for instance in fixtures:
        check(instance['kind'] + '-synthetic-structural-only', validator.is_valid(instance))
        for key in instance:
            candidate = copy.deepcopy(instance)
            del candidate[key]
            check(instance['kind'] + '-missing-' + key, not validator.is_valid(candidate))
        for key, value in [('unknown', 'x'), ('version', None), ('version', 1), ('version', True)]:
            candidate = dict(instance, **{key: value})
            check(instance['kind'] + '-bad-' + key + '-' + repr(value), not validator.is_valid(candidate))

    mutations = [('zero-hash', ('geometry_sha256',), '0' * 64),
                 ('wrong-ref-kind', ('algorithm_ref', 'schema_id'), 'ss-ttl-v1'),
                 ('extra-ref', ('algorithm_ref', 'path'), 'x'),
                 ('backend', ('twiddle_backend',), 'unbound'),
                 ('slug-newline', ('profile_id',), 'a\n')]
    for name, path, value in mutations:
        candidate = copy.deepcopy(numeric)
        node = candidate
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = value
        check(name, not validator.is_valid(candidate))
    for value in ['01', '-0', '+1', '1e1', '1.0', '1\n', 1, True, None]:
        candidate = copy.deepcopy(geometry)
        candidate['mics'][0]['x']['numerator'] = value
        check('bad-integer-' + repr(value), not validator.is_valid(candidate))
    candidate = copy.deepcopy(geometry)
    candidate['mics'].reverse()
    check('mic-order', not validator.is_valid(candidate))
    for pair in [('2', '4'), ('0', '2')]:
        candidate = copy.deepcopy(geometry)
        candidate['mics'][0]['x'] = rational(*pair)
        check('schema-alone-allows-unreduced-' + str(pair), validator.is_valid(candidate))
        check('semantic-gcd-rejects-' + str(pair), gcd(abs(int(pair[0])), int(pair[1])) != 1)

    raw_a = b'{"name":"A"}'
    raw_b = b'{"name":"\\u0041"}'
    prefix = b'SoundSight/config/v1\n'
    digest = lambda data: hashlib.sha256(data).hexdigest()
    check('B-raw-literal-digest', digest(prefix + raw_a) == 'b1514fe9c6a93bd8bcbb7e2a7d426670c533557a8d93c08cd177f705673e649e')
    check('B-raw-escaped-digest', digest(prefix + raw_b) == '3894d84e5c07edcecef45348a2dd096df21f3fe97612217fb7a07eeba4c0fa0c')
    check('B-counterexample-normalizes', canonical(raw_a) == canonical(raw_b) == raw_a)
    check('counterexample-not-production', not validator.is_valid(json.loads(raw_a)))
    check('ASCII-escapes', encode('"\\/\t\n\x00\x1f\x7f') == '"\\"\\\\/\\u0009\\u000a\\u0000\\u001f\\u007f"')
    check('sort-keys-keep-array', canonical(b' {"z":["2","1"],"a":"\\/"} \n') == b'{"a":"/","z":["2","1"]}')
    for name, raw in [('duplicate', b'{"A":"x","\\u0041":"y"}'),
                      ('BOM', b'\xef\xbb\xbf{}'), ('nonascii', b'{"x":"\\u0080"}'),
                      ('number', b'{"x":1}'), ('float', b'{"x":1.5}'),
                      ('bool', b'{"x":true}'), ('null', b'{"x":null}'),
                      ('NaN', b'{"x":NaN}'), ('invalid-utf8', b'{"x":"\xff"}')]:
        rejected('parse-encode-reject-' + name, lambda raw=raw: canonical(raw))
    report = dict(status='FINITE_DOCUMENT_PROBES_PASS_NOT_PRODUCTION', checks=checks,
                  count=len(checks), schema_sha256=digest(schema_bytes),
                  checker_sha256=digest(Path(__file__).read_bytes()),
                  python=sys.version, jsonschema=version, synthetic_only=True,
                  production_frozen=False, missing_external_schemas=True,
                  not_tested=['external reference resolution and recursive DAG verifier',
                              'full geometry/cross-root semantics', 'production encoder',
                              'C token counterexample execution', 'RTL/EDA/ARM/board'],
                  b_review='https://github.com/TophBeifong1744/Competition_fpga/pull/30#issuecomment-5810446729')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ['status', 'count', 'schema_sha256']}))


if __name__ == '__main__':
    main()
