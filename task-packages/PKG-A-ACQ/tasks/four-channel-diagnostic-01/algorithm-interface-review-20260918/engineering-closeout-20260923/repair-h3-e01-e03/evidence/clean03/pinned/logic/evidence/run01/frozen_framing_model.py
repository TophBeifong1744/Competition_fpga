"""Independent functional reference for the BRAM-friendly 1024/512 framer."""
from dataclasses import dataclass

N = 1024
HOP = 512
PACKET_GROUPS = 250
MIN24 = -(1 << 23)
MAX24 = (1 << 23) - 1


@dataclass(frozen=True)
class Group:
    sample_id: int
    pcm: tuple[int, int, int, int]
    flags: int = 0
    reserved: int = 0
    integrity_error: bool = False
    source_flags: int = 0


@dataclass(frozen=True)
class Frame:
    session_id: int
    frame_index: int
    interval_index: int
    reset_before: bool
    samples: tuple[Group, ...]

    @property
    def first_id(self):
        return self.samples[0].sample_id

    @property
    def last_id(self):
        return self.samples[-1].sample_id


@dataclass(frozen=True)
class Event:
    code: str
    session_id: int
    sample_id: int | None
    prev_id: int | None
    raw_flags: int
    source_flags: int
    unused_tail: int
    interval_index: int


class Framer:
    def __init__(self):
        self.active = False
        self.frames = []
        self.events = []

    def start(self, session_id):
        if self.active:
            raise ValueError("session already active")
        self.active = True
        self.session_id = session_id
        self.frame_index = 0
        self.interval_index = 0
        self.window = []
        self.prev_id = None
        self.have_frame = False
        self.new_count = 0
        self.reset_next = True

    def _tail(self):
        return self.new_count if self.have_frame else len(self.window)

    def push(self, group):
        if not self.active:
            raise ValueError("no active session")
        code = None
        if group.integrity_error or group.source_flags:
            code = "upstream"
        elif self.prev_id is not None and group.sample_id != self.prev_id + 1:
            code = "id"
        elif group.flags & ~0xF or group.reserved:
            code = "flags"
        elif len(group.pcm) != 4 or any(not MIN24 <= x <= MAX24 for x in group.pcm):
            code = "range"
        if code:
            self.events.append(Event(code, self.session_id, group.sample_id,
                                     self.prev_id, group.flags, group.source_flags,
                                     self._tail(), self.interval_index))
            self.interval_index += 1
            self.window = []
            self.prev_id = None
            self.have_frame = False
            self.new_count = 0
            self.reset_next = True
            return
        self.window.append(group)
        self.prev_id = group.sample_id
        self.new_count += 1
        if len(self.window) == N:
            self.frames.append(Frame(self.session_id, self.frame_index,
                                     self.interval_index, self.reset_next,
                                     tuple(self.window)))
            self.frame_index += 1
            self.window = self.window[HOP:]
            self.have_frame = True
            self.new_count = 0
            self.reset_next = False

    def stop(self):
        if not self.active:
            raise ValueError("no active session")
        self.events.append(Event("stop", self.session_id, self.prev_id,
                                 self.prev_id, 0, 0, self._tail(),
                                 self.interval_index))
        self.active = False
