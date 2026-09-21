"""Conditional design models, NOT a PS driver or synthesizable hardware."""
from dataclasses import dataclass
from fractions import Fraction
from math import ceil

MAX_ID = (1 << 64) - 1


class Ownership:
    def __init__(self, capacity=8):
        self.slots = ['FREE', 'FREE']
        self.queue = []
        self.capacity = capacity
        self.failed = None

    def arm(self, slot):
        if self.failed or self.slots[slot] != 'FREE':
            raise ValueError('OWNERSHIP')
        self.slots[slot] = 'DMA'

    def complete(self, slot):
        if self.slots[slot] != 'DMA':
            raise ValueError('OWNERSHIP')
        self.slots[slot] = 'CPU'

    def copy(self, slot, payload):
        if self.failed or self.slots[slot] != 'CPU':
            raise ValueError('OWNERSHIP')
        if len(self.queue) == self.capacity:
            self.failed = 'QUEUE_OVERFLOW'
            raise ValueError(self.failed)  # CPU ownership retained, no overwrite
        self.queue.append(bytes(payload))  # independent immutable copy
        self.slots[slot] = 'FREE'

    def release_head(self):
        if not self.queue:
            raise ValueError('EMPTY')
        return self.queue.pop(0)


class Results:
    def __init__(self, epoch_limit=(1 << 32)-1):
        self.epoch = 0
        self.limit = epoch_limit
        self.interval = 0
        self.active = False
        self.entries = {}
        self.audit = []
        self.failed = False
        self.await_clean = False

    def start(self):
        if self.active or self.failed or self.epoch == self.limit:
            raise ValueError('SESSION_REUSE_OR_OVERFLOW')
        self.epoch += 1
        self.interval = 0
        self.active = True
        self.await_clean = False

    def submit(self, frame, last_id, ttl, bindings):
        key = (self.epoch, self.interval, frame)
        if not self.active or self.await_clean or key in self.entries or not 0 <= frame < (1 << 32):
            raise ValueError('IDENTITY')
        if ttl < 0 or not 0 <= last_id <= MAX_ID or last_id + ttl > MAX_ID:
            raise ValueError('TTL_OVERFLOW')
        self.entries[key] = dict(last_id=last_id, expiry=last_id+ttl, bindings=bindings, state='PENDING')
        return key

    def barrier(self, reason, fatal=False):
        for entry in self.entries.values():
            if entry['state'] in ('PENDING', 'COMMITTED'):
                entry['state'] = 'REVOKED'
        self.audit.append(reason)
        if fatal:
            self.failed = True
            self.active = False
        elif reason in ('STOP', 'RESET'):
            self.active = False
        else:
            self.await_clean = True

    def begin_clean_interval(self):
        if not self.active:
            raise ValueError('INACTIVE_SESSION')
        if self.await_clean:
            if self.interval == (1 << 32)-1:
                self.barrier('INTERVAL_OVERFLOW', fatal=True)
                raise ValueError('INTERVAL_OVERFLOW')
            self.interval += 1
            self.await_clean = False

    def finish(self, key, now_id, bindings, *, status=False, error=False, stop=False):
        if stop:
            self.barrier('STOP')
            return 'REVOKED'
        entry = self.entries.get(key)
        if entry is None:
            return 'UNKNOWN_ID_REJECT'
        if error:
            committed = entry['state'] == 'COMMITTED'
            entry['state'] = 'REVOKED'
            self.audit.append(('LATE_ERROR' if committed else 'FRAME_ERROR', key))
            if committed:
                self.barrier('POST_COMMIT_FAIL_STOP', fatal=True)
            return 'REVOKED'
        if entry['state'] != 'PENDING':
            return 'NO_COMMIT'
        if not self.active or key[:2] != (self.epoch, self.interval) or bindings != entry['bindings']:
            entry['state'] = 'REVOKED'
            return 'REVOKED'
        if now_id is None or not status:
            return 'WAIT'
        if now_id < entry['last_id']:
            return 'INVALID_TIME'
        if now_id > entry['expiry']:
            entry['state'] = 'EXPIRED'
            return 'EXPIRED'
        entry['state'] = 'COMMITTED'
        return 'COMMITTED'


def sample_upper_bound(anchor_id, elapsed_us, uncertainty_samples):
    """Conservative within one unchanged 48 kHz epoch; anchor must be fresh."""
    if min(anchor_id, elapsed_us, uncertainty_samples) < 0:
        raise ValueError('CLOCK')
    upper = anchor_id + ceil(Fraction(elapsed_us*48000, 1000000)) + uncertainty_samples
    if upper > MAX_ID:
        raise ValueError('CLOCK_OVERFLOW')
    return upper


def validate_ifft_half(half):
    """Proposed boundary guard only; does not alter B conjugation or golden."""
    if len(half) != 513 or any(len(row) != 2 for row in half):
        raise ValueError('HALF_SHAPE')
    if any(type(v) is not int or not -(1<<24) <= v < (1<<24) for row in half for v in row):
        raise ValueError('S25_RANGE')
    if half[0][1] or half[512][1]:
        raise ValueError('NONREAL_ENDPOINT')
    if any(row[1] == -(1<<24) for row in half[1:512]):
        raise ValueError('CONJUGATE_OVERFLOW')


def validate_layout(regions, capacity):
    previous = 0
    for r in regions:
        if r['offset'] % 64 or r['offset'] < previous or r['end'] <= r['offset'] or r['end'] > capacity:
            raise ValueError('MEMORY_LAYOUT')
        previous = r['end']
    return True


def queue_trace(arrivals, service_cycles, capacity):
    """FIFO, one consumer, completed-at-arrival departs first. Capacity includes in-flight."""
    if capacity < 1 or service_cycles is None:
        raise ValueError('UNBOUNDED_SERVICE')
    if service_cycles <= 0 or any(b < a for a, b in zip(arrivals, arrivals[1:])):
        raise ValueError('SCHEDULE')
    ends, high = [], 0
    for tick in arrivals:
        ends = [x for x in ends if x > tick]
        if len(ends) >= capacity:
            raise ValueError('QUEUE_FULL')
        ends.append(max(tick, ends[-1] if ends else tick)+service_cycles)
        high = max(high, len(ends))
    return high


@dataclass(frozen=True)
class Stage:
    name: str
    resource: str
    cycles: int
    after: tuple


def serial_schedule(stages):
    ends, resources, rows = {}, {}, []
    for s in stages:
        if s.cycles < 0 or any(p not in ends for p in s.after):
            raise ValueError('DEPENDENCY_OR_CYCLES')
        begin = max([resources.get(s.resource, 0)] + [ends[p] for p in s.after])
        end = begin + s.cycles
        resources[s.resource] = end
        ends[s.name] = end
        rows.append(dict(name=s.name, resource=s.resource, begin=begin, end=end, cycles=s.cycles))
    return rows


def budget(mult25=25, mult51=51, wide_mult=75, external_wait=0):
    """Single nonoverlapped ALU / RAM schedule. Mult cost is a DESIGN ASSUMPTION.
    Baseline shift-add multiplier uses operand-bit iterations; wide adder timing
    and historical IP slots are NOT certified worst-case hardware bounds.
    """
    if min(mult25, mult51, wide_mult) < 1 or external_wait is None:
        return dict(total='REALTIME_BLOCKED', reason='UNBOUNDED_SERVICE')
    costs = [
        ('copy_check', 250*8*4 + 512*8*4),
        ('accepted_frame', 512*8 + 1024*8),
        ('mean', 4*1023+4*10+4096),
        ('window', 8192*(mult25+2)),
        ('fft_slots', 8*7366),
        ('adapt', 8*513*2*2),
        ('gate_power', 528*(mult25+1)+4*(66+104)+32),
        ('cross', 3078*(4*mult25+2)),
        ('power_mask', 3078*(2*mult51+1)+474*13+6*78),
        ('phat', 474*(75*3+2*(2*wide_mult+4)+2*wide_mult+8)),
        ('conjugate', 6*1024*2),
        ('ifft_slots', 6*7406),
        ('lag', 86*2+6*(2*64+6+wide_mult)),
        ('doa', 6*(4*wide_mult+64+20)+2*(wide_mult+64)+24*4+2*wide_mult),
        ('das_delay_generation', 2*24*4+8*(wide_mult+18)),
        ('das_two_beams', 2*512*4*(2*mult25+4)+512*(2*mult25+4)),
        ('config_status', 14*16+64),
        ('cdc_protocol', 14*8),
        ('queue_bookkeeping', 1024),
        ('external_service_wait', external_wait),
    ]
    stages = [Stage(name, 'serial_shared', count, (() if i == 0 else (costs[i-1][0],))) for i,(name,count) in enumerate(costs)]
    rows = serial_schedule(stages)
    total = rows[-1]['end']
    hop = 100000000*512//48000
    return dict(total='REALTIME_BLOCKED', conditional_cycles=total, hop_cycles=hop,
                conditional_deadline_met=total <= hop, rows=rows,
                assumptions=dict(mult25=mult25, mult51=mult51, wide_mult=wide_mult,
                                 external_wait=external_wait, alu_ii='serialized', clock_hz=100000000),
                not_evidenced=['PS WCET', 'DDR arbitration', 'IP service bound', 'wide ALU timing', 'CDC', 'output service'])


def memory_plan():
    # Proposed logical CPU-side storage, not linker placement or FPGA primitive use.
    sizes = [('rx_slots', 2*8064), ('accepted_packet_ring', 8*8064),
             ('frame_workspaces', 2*(1024*32+128)), ('two_spectra', 2*4*513*8),
             ('phat_pair', 513*8+128), ('ifft_work', 1024*8+128),
             ('correlation', 1024*4+128), ('audio_history_lookahead', 18*4*4+128),
             ('output_hop', 512*4+128), ('descriptors', 4096)]
    cursor, regions = 0, []
    for name, size in sizes:
        cursor = (cursor+63)//64*64
        regions.append(dict(name=name, offset=cursor, end=cursor+size, bytes=size))
        cursor += size
    return dict(regions=regions, logical_bytes=cursor, capacity=1<<20,
                fits=cursor <= (1<<20), actual_addresses='UNASSIGNED_NOT_LINKED',
                excludes=['IP internal BRAM', 'program/heap/stack', 'PL framer cache if selected'])
