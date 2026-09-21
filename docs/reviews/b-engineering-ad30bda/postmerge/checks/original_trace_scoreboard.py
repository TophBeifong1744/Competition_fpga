"""Offline candidate trace checker, NOT an implementation or CDC proof.

Each row is a sampled output-interface tick with monotonic capture tick and
physical audio `now` in current-session sample units. Events describe the
result transaction, not FFT data beats. reset/fatal is applied before commit.
"""
import argparse
import json
from pathlib import Path


class TraceError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise TraceError(reason)


def uint(value):
    return type(value) is int and 0 <= value < 2**64


def check(rows, *, max_stall_ticks, expected_units=('fft', 'ifft')):
    require(type(max_stall_ticks) is int and max_stall_ticks >= 0, 'finite stall bound required')
    require(bool(expected_units) and all(isinstance(v, str) for v in expected_units)
            and len(set(expected_units)) == len(expected_units), 'external expected units required')
    epoch = None
    used_sessions = set()
    pending = None
    stall = 0
    last_tick = -1
    last_now = -1
    last_emit = -1
    transactions = {}
    config = None
    dead = False
    counts = dict(commits=0, accepted=0, resets=0, late_errors=0, stale_callbacks=0)
    for row in rows:
        tick, now = row['tick'], row['now']
        require(uint(tick) and tick == last_tick + 1, 'capture must include every tick starting at zero')
        last_tick = tick
        if row.get('reset', False):
            epoch = row['session']
            require(isinstance(epoch, str) and epoch and epoch not in used_sessions, 'new unique session required')
            used_sessions.add(epoch)
            pending, stall, config, dead = None, 0, None, False
            last_now = last_emit = -1
            counts['resets'] += 1
        require(epoch is not None and row['session'] == epoch, 'session mismatch')
        require(uint(now) and now >= last_now, 'physical sample clock reversed')
        last_now = now
        fatal = row.get('fatal', False)
        if fatal:
            dead, pending, stall = True, None, 0
        # Events in the same tick precede commit; no data-valid surrogate for final status.
        # Capture array order must not let a commit outrun a same-tick fault.
        events = sorted(row.get('events', []), key=lambda e: {'submit': 0, 'status': 1, 'error': 1, 'commit': 2}.get(e['kind'], 1))
        for event in events:
            key = (event['session'], event['frame'])
            require(uint(event['frame']), 'invalid frame identity')
            if event['session'] != epoch:
                counts['stale_callbacks'] += 1
                require(event['kind'] in ('status', 'error'), 'old session cannot submit/commit')
                continue
            kind = event['kind']
            if kind == 'submit':
                require(not dead and key not in transactions, 'dead or duplicate submit')
                expected = event['expected']
                require(isinstance(expected, list) and expected and all(isinstance(v, str) for v in expected)
                        and len(set(expected)) == len(expected), 'invalid expected status set')
                require(set(expected) == set(expected_units), 'trace cannot weaken external completion contract')
                require(isinstance(event['config'], str) and bool(event['config']), 'config hash required')
                if config is None:
                    config = event['config']
                require(config == event['config'], 'session config changed')
                transactions[key] = dict(expected=set(expected), done=set(), bad=False, committed=False,
                                         config=config)
            else:
                require(key in transactions, 'unknown transaction')
                tx = transactions[key]
                if kind == 'status':
                    require(event['unit'] in tx['expected'] and event['unit'] not in tx['done'], 'unknown/duplicate final status')
                    tx['done'].add(event['unit'])
                    if event.get('error', False):
                        tx['bad'] = True
                        if tx['committed']:
                            dead = True
                            counts['late_errors'] += 1
                elif kind == 'error':
                    tx['bad'] = True
                    if tx['committed']:
                        dead = True
                        counts['late_errors'] += 1
                elif kind == 'commit':
                    require(not dead and not tx['bad'] and not tx['committed'] and tx['done'] == tx['expected'], 'non-atomic commit')
                    require(event['config'] == tx['config'], 'commit config mismatch')
                    available, expiry = event['available'], event['valid_through']
                    require(uint(available) and uint(expiry) and available <= now <= expiry, 'future or expired commit')
                    tx['committed'] = True
                    counts['commits'] += 1
                else:
                    raise TraceError('unknown event')
        valid, ready = row['valid'], row['ready']
        require(type(valid) is bool and type(ready) is bool, 'boolean handshake required')
        if dead:
            require(not valid, 'fatal session must not publish')
            pending, stall = None, 0
            continue
        payload = row.get('payload')
        if pending is not None:
            require(valid and payload == pending, 'payload/valid changed under backpressure')
        if valid:
            require(payload['session'] == epoch, 'stale output')
            emit = payload['emit']
            require(uint(emit) and emit == last_emit + 1, 'output identity gap/duplicate')
            require(payload['source_sample'] == emit - 8, '8-sample profile identity mismatch')
            require(payload['available'] == emit and now >= emit, 'output before availability')
            require(type(payload['pcm']) is int and -(2**23) <= payload['pcm'] < 2**23, 'non-S24 output')
            if ready:
                last_emit, pending, stall = emit, None, 0
                counts['accepted'] += 1
            else:
                pending = dict(payload)
                stall += 1
                require(stall <= max_stall_ticks, 'bounded backpressure exceeded')
        else:
            stall = 0
    require(pending is None, 'capture ended before drain/cancel')
    return dict(status='TRACE_MATCHES_CANDIDATE_ONLY', **counts)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('trace', type=Path)
    p.add_argument('--max-stall-ticks', type=int, required=True)
    p.add_argument('--expected-units', nargs='+', required=True)
    a = p.parse_args()
    print(json.dumps(check(json.loads(a.trace.read_text(encoding='utf-8')), max_stall_ticks=a.max_stall_ticks,
                           expected_units=a.expected_units)))
