"""Declared C same-domain semantics; no MMIO, byte offsets or CPU ABI."""
from dataclasses import dataclass
from typing import Protocol
from .contracts import integer, require
from .records import C_NATIVE_VERSION


NATIVE_OPS = {"CONFIG": 1, "RUN": 2, "STOP": 3, "RECOVER": 4}


@dataclass(frozen=True)
class NativeCommand:
    operation: str
    context160: int
    map96: int
    timeout_cycles: int
    native_version: str

    def validate(self):
        # 中文用途：只核同域payload宽度，不把有效握手命令变成未批准CPU寄存器。
        require(self.native_version == C_NATIVE_VERSION and self.operation in NATIVE_OPS,
                "native command version/operation")
        integer(self.context160, "context160", 0, (1 << 160) - 1)
        integer(self.map96, "map96", 0, (1 << 96) - 1)
        require(self.map96 >> 83 == 0, "reserved map bits")
        integer(self.timeout_cycles, "native timeout cycles", 1, 8388608)
        return self


class CpuControlAdapter(Protocol):
    """Future implementation must bind atomicity, access types and side effects."""
    cpu_schema_id: str
    adapter_version: str
    native_version: str

    def command(self, command: NativeCommand): ...
    def atomic_snapshot(self): ...
    def request_safe_stop(self): ...


CPU_ADDRESS_MAP = "UNBOUND"
IRQ_PROTOCOL = "UNBOUND"
SAFE_STATE = "SOFTWARE_REFUSAL; no motion arm/enable adapter"
