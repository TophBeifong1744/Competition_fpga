"""Independent repair of the engineering Results model; not production ABI."""
MAX_ID = (1 << 64) - 1


def freeze(value):
    """Typed recursive immutable value; no arbitrary object/string coercion."""
    if type(value) in (str, int, bool, bytes, type(None)):
        return (type(value).__name__, value)
    if type(value) in (list, tuple):
        return (type(value).__name__, tuple(freeze(x) for x in value))
    if type(value) is dict and all(type(k) is str for k in value):
        return ('dict', tuple((k, freeze(value[k])) for k in sorted(value)))
    raise ValueError('UNSUPPORTED_BINDING')


class Results:
    def __init__(self, epoch_limit=(1 << 32)-1):
        self.epoch = 0
        self.limit = epoch_limit
        self.interval = 0
        self.active = self.failed = self.await_clean = False
        self.entries = {}
        self.audit = []
        self._config = None

    def start(self):
        if self.active or self.failed or self.epoch >= self.limit:
            raise ValueError('SESSION_REUSE_OR_OVERFLOW')
        self.epoch += 1
        self.interval = 0
        self.active = True
        self.await_clean = False
        self._config = None  # First accepted submit binds this session, once.

    def submit(self, frame, last_id, ttl, bindings):
        key = (self.epoch, self.interval, frame)
        if not self.active or self.await_clean or key in self.entries or type(frame) is not int or not 0 <= frame < (1 << 32):
            raise ValueError('IDENTITY')
        if type(last_id) is not int or type(ttl) is not int or ttl < 0 or not 0 <= last_id <= MAX_ID or last_id + ttl > MAX_ID:
            raise ValueError('TTL_OVERFLOW')
        snapshot = freeze(bindings)
        if self._config is not None and snapshot != self._config:
            raise ValueError('SESSION_CONFIG_CHANGE')
        self._config = snapshot
        self.entries[key] = dict(last_id=last_id, expiry=last_id+ttl,
                                 bindings=snapshot, state='PENDING', ever_committed=False)
        return key

    def barrier(self, reason, fatal=False):
        for key, entry in self.entries.items():
            if key[0] == self.epoch and entry['state'] in ('PENDING', 'COMMITTED'):
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
        # stop is a current-session control request, not a callback's epoch.
        if stop:
            self.barrier('STOP')
        entry = self.entries.get(key)
        if entry is None:
            return 'UNKNOWN_ID_REJECT'
        if error:
            entry['state'] = 'REVOKED'
            historical = entry['ever_committed']
            old = key[0] != self.epoch
            self.audit.append(('OLD_SESSION_LATE_ERROR' if old else
                               'LATE_ERROR' if historical else 'FRAME_ERROR', key))
            if historical and not old:
                self.barrier('POST_COMMIT_FAIL_STOP', fatal=True)
            return 'REVOKED'
        if stop:
            return 'REVOKED'
        if entry['state'] != 'PENDING':
            return 'NO_COMMIT'
        if not self.active or key[:2] != (self.epoch, self.interval) or freeze(bindings) != entry['bindings']:
            entry['state'] = 'REVOKED'
            return 'REVOKED'
        if now_id is None or not status:
            return 'WAIT'
        if type(now_id) is not int or not 0 <= now_id <= MAX_ID or now_id < entry['last_id']:
            return 'INVALID_TIME'
        if now_id > entry['expiry']:
            entry['state'] = 'EXPIRED'
            return 'EXPIRED'
        entry['state'] = 'COMMITTED'
        entry['ever_committed'] = True
        return 'COMMITTED'
