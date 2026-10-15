"""Explicit configuration and static artifact identity, never loaded identity."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PureWindowsPath


class ProtocolError(Exception):
    """Rejected configuration, event or ownership transition."""


class Refusal(ProtocolError):
    """Admission is unavailable; no physical action has occurred."""


def require(condition, reason):
    if not condition:
        raise ProtocolError(reason)


def integer(value, name, minimum=0, maximum=None):
    require(type(value) is int and value >= minimum and
            (maximum is None or value <= maximum), "invalid integer: " + name)
    return value


def keys(value, required, optional=()):
    require(isinstance(value, dict), "object required")
    require(set(required) <= set(value) <= set(required) | set(optional),
            "missing or unsupported fields: " + str(sorted(set(value))))


def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), "missing text: " + name)
    return value


def boolean(value, name):
    require(type(value) is bool, "boolean required: " + name)
    return value


def read_json(path):
    # 中文用途：拒绝重复键和非有限JSON值，避免合同被隐式覆盖。
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject(value):
        raise ProtocolError("nonfinite JSON: " + value)
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=unique, parse_constant=reject)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_identity(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "regular input file required")
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": sha256(data)}


def inside(root, relative):
    root = Path(root).resolve(strict=True)
    require(root.is_dir(), "artifact root is not a directory")
    rel = Path(text(relative, "artifact path"))
    windows_rel = PureWindowsPath(relative)
    require(not (rel.drive or rel.root or rel.anchor or
                 windows_rel.drive or windows_rel.root or windows_rel.anchor) and
            ".." not in rel.parts and ".." not in windows_rel.parts, "unsafe relative path")
    candidate = root / rel
    # 中文用途：拒绝盘符/根锚后按有限相对段检查链接，避免parent停在自身而循环。
    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), "symlink input forbidden")
    resolved = candidate.resolve(strict=True)
    # 中文用途：用Python 3.8路径API保持解析后的根边界拒绝。
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ProtocolError("artifact outside root/file") from None
    require(resolved.is_file(), "artifact outside root/file")
    return resolved


def inspect_artifacts(root, declarations):
    require(isinstance(declarations, list), "artifacts must be a list")
    result, kinds, paths = [], set(), set()
    for item in declarations:
        keys(item, ("kind", "path", "bytes", "sha256", "build_id"))
        require(item["kind"] in {"bit", "hwh", "manifest", "xsa", "dtbo", "ltx"},
                "unsupported artifact kind")
        require(item["kind"] not in kinds and item["path"] not in paths, "duplicate artifact")
        path = inside(root, item["path"])
        require(path.suffix.lower() == "." + ("json" if item["kind"] == "manifest" else item["kind"]),
                "artifact extension/type mismatch")
        actual = file_identity(path)
        integer(item["bytes"], "artifact bytes", 1)
        require(actual["bytes"] == item["bytes"] and actual["sha256"] == item["sha256"],
                "artifact identity mismatch")
        text(item["build_id"], "build_id")
        kinds.add(item["kind"])
        paths.add(item["path"])
        result.append(dict(item, actual=actual))
    if declarations:
        require({"bit", "hwh", "manifest"} <= kinds, "bit/hwh/manifest required together")
        require(len({item["build_id"] for item in declarations}) == 1, "mixed build declarations")
        pair = {item["kind"]: Path(item["path"]) for item in declarations}
        require(pair["bit"].parent == pair["hwh"].parent and pair["bit"].stem == pair["hwh"].stem,
                "bit/HWH must be adjacent and same name")
    return {"evidence_level": "STATIC_DECLARATIONS_ONLY", "loaded_identity": "UNKNOWN", "artifacts": result}


@dataclass(frozen=True)
class Identity:
    boot: int
    session: str
    epoch: int
    generation: int
    transaction: int

    def as_dict(self):
        return dict(boot=self.boot, session=self.session, epoch=self.epoch,
                    generation=self.generation, transaction=self.transaction)


@dataclass(frozen=True)
class Profile:
    _data: dict

    @property
    def data(self):
        return json.loads(json.dumps(self._data))

    @classmethod
    def parse(cls, value):
        keys(value, ("schema_version", "scope", "transport", "raw_schema", "boot", "epoch",
                     "generation", "deadlines", "dma", "queue_limit", "artifacts", "declarations"))
        require(value["schema_version"] == 1 and type(value["schema_version"]) is int, "profile version")
        require(value["scope"] == "SYNTHETIC_TEST" and value["transport"] == "TEST_TRANSPORT",
                "only explicit test scope is supported")
        require(value["raw_schema"] == "raw32-le-s24-v1", "raw schema unsupported")
        for name in ("boot", "epoch", "generation"):
            integer(value[name], name, 0, (1 << 64) - 1)
        integer(value["queue_limit"], "queue_limit", 1)
        deadlines = value["deadlines"]
        keys(deadlines, ("domain", "unit", "poll", "arm", "transfer", "stop", "abort", "archive"))
        require(deadlines["domain"] == "SYNTHETIC_TICK" and deadlines["unit"] == "ticks", "deadline domain")
        for name in ("poll", "arm", "transfer", "stop", "abort", "archive"):
            integer(deadlines[name], name, 1)
        dma = value["dma"]
        keys(dma, ("mode", "s2mm", "mm2s", "sg", "dre", "memory_width_bits", "axis_width_bits",
                   "length_width_bits", "length_granularity", "cache_line_bytes", "packet_bytes", "slots"))
        require(dma["mode"] == "simple" and dma["s2mm"] is True and dma["mm2s"] is False and
                dma["sg"] is False and dma["dre"] is False, "unsupported DMA mode")
        width = integer(dma["memory_width_bits"], "memory_width_bits", 8)
        require(width % 8 == 0, "memory width not byte aligned")
        require(type(dma["axis_width_bits"]) is int and dma["axis_width_bits"] == 32, "AXIS width")
        length_width = integer(dma["length_width_bits"], "length_width_bits", 1, 64)
        gran = integer(dma["length_granularity"], "length_granularity", 1)
        line = integer(dma["cache_line_bytes"], "cache_line_bytes", 1)
        packet = integer(dma["packet_bytes"], "packet_bytes", 32, (1 << length_width) - 1)
        require(packet % 32 == 0 and packet % gran == 0, "packet granularity")
        require(isinstance(dma["slots"], list) and dma["slots"], "slots required")
        intervals, names = [], set()
        for slot in dma["slots"]:
            keys(slot, ("name", "address", "capacity"))
            name = text(slot["name"], "slot.name")
            require(name not in names, "duplicate slot")
            names.add(name)
            address = integer(slot["address"], "address")
            capacity = integer(slot["capacity"], "capacity", packet)
            require(address % (width // 8) == 0 and address % line == 0 and capacity % line == 0,
                    "noDRE memory/cache alignment")
            require(address + capacity <= 1 << 64, "address interval overflow")
            require(all(address + capacity <= a or address >= b for a, b in intervals), "overlapping buffers")
            intervals.append((address, address + capacity))
        keys(value["declarations"], ("part", "image_identity", "cpu_wire_schema", "ps_time_bound"))
        require(value["declarations"]["cpu_wire_schema"] == "UNBOUND" and
                value["declarations"]["ps_time_bound"] == "UNKNOWN", "test declaration cannot bind CPU/time")
        for name in ("part", "image_identity"):
            text(value["declarations"][name], name)
        require(isinstance(value["artifacts"], list), "artifact declarations required")
        # 中文用途：深复制冻结调用者配置，防止后续修改绕过校验。
        return cls(json.loads(json.dumps(value)))

    def deadline(self, name):
        return self._data["deadlines"][name]


def hardware_admission(*_args, **_kwargs):
    raise Refusal("HARDWARE_ADAPTER_UNBOUND: image, allocator, cache/barriers, status/abort and CPU address schema required")
