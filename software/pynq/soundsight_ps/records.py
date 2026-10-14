"""Lossless acquisition records and version-bound native observations."""
from dataclasses import dataclass
import struct
from typing import Protocol
from .contracts import keys, require, integer, boolean, text

RAW_SCHEMA = "raw32-le-s24-v1"
C_NATIVE_VERSION = "b529fed84bde1d5d5d6326e0d8870416c738657a"
BANK_WORDS = (37, 41, 38, 27, 32)


@dataclass(frozen=True)
class RawFrame:
    source_id: int
    microphones: tuple
    clip_flags: int
    reserved: int
    raw: bytes

    def as_dict(self):
        return {"source_id": self.source_id, "microphones": list(self.microphones),
                "clip_flags": self.clip_flags, "reserved": self.reserved}


def decode_raw(raw):
    require(type(raw) is bytes and len(raw) > 0 and len(raw) % 32 == 0, "whole nonempty raw32 packet required")
    result = []
    # 中文用途：保留原uint64帧号和整数码，clip仅作标记，不归一化或补样。
    for offset in range(0, len(raw), 32):
        chunk = raw[offset:offset + 32]
        lo, hi, *rest = struct.unpack("<IIiiiiII", chunk)
        microphones, flags, reserved = tuple(rest[:4]), rest[4], rest[5]
        require(all(-(1 << 23) <= sample < (1 << 23) for sample in microphones), "invalid signed24 extension")
        require(flags & ~15 == 0 and reserved == 0, "raw reserved bits")
        result.append(RawFrame(lo | hi << 32, microphones, flags, reserved, chunk))
    return tuple(result)


@dataclass(frozen=True)
class OpaqueCpuRecord:
    schema_id: str
    adapter_version: str
    payload: bytes


class CpuRecordAdapter(Protocol):
    """Future binding must define framing/atomicity/ACK; no CPU layout inferred."""
    schema_id: str
    adapter_version: str

    def decode(self, record: OpaqueCpuRecord): ...


def native_record(value):
    keys(value, ("envelope", "native_version", "kind", "fields"))
    require(value["envelope"] == "SYNTHETIC_TEST/TEST_TRANSPORT" and
            value["native_version"] == C_NATIVE_VERSION, "unbound native envelope/version")
    fields = value["fields"]
    if value["kind"] == "diagnostic_word":
        keys(fields, ("bank", "sequence", "word", "words", "last", "data"))
        bank = integer(fields["bank"], "bank", 0, 4)
        integer(fields["sequence"], "sequence", 0, (1 << 64) - 1)
        integer(fields["word"], "word", 0, BANK_WORDS[bank] - 1)
        require(type(fields["words"]) is int and fields["words"] == BANK_WORDS[bank], "native bank length")
        boolean(fields["last"], "last")
        require(fields["last"] == (fields["word"] + 1 == fields["words"]), "native last mismatch")
        integer(fields["data"], "data", 0, (1 << 32) - 1)
    elif value["kind"] == "result":
        keys(fields, ("valid", "abort", "eligible", "identity", "angle_q8", "angle_deg"))
        for name in ("valid", "abort", "eligible"):
            boolean(fields[name], name)
        require(fields["valid"] or fields["abort"], "no native event")
        integer(fields["identity"], "identity725", 0, (1 << 725) - 1)
        integer(fields["angle_q8"], "S18Q8", -(1 << 17), (1 << 17) - 1)
        integer(fields["angle_deg"], "U9", 0, 511)
    else:
        require(False, "unsupported native record kind")
    return value
