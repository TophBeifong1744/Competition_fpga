#!/usr/bin/env python3
"""Run bounded, profile-declared PYNQ Overlay identity and DMA loopback tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_profile import read_json, resolve, sha256, validate


def read_device_tree(name: str) -> str:
    path = Path("/sys/firmware/devicetree/base") / name
    if not path.is_file():
        return "unavailable"
    return path.read_bytes().replace(b"\x00", b",").decode("utf-8", errors="replace").strip(",")


def find_key(mapping: dict[str, Any], requested: str) -> str:
    candidates = [key for key in mapping if key == requested or key.endswith("/" + requested)]
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one HWH IP matching {requested!r}, found {candidates}")
    return candidates[0]


def resolve_attr(root: Any, path: str) -> Any:
    current = root
    for part in path.replace("/", ".").split("."):
        if part:
            current = getattr(current, part)
    return current


def pattern_bytes(kind: str, length: int) -> bytes:
    if kind == "counter8":
        return bytes(index & 0xFF for index in range(length))
    if kind == "alternating":
        return bytes(0xA5 if index % 2 == 0 else 0x5A for index in range(length))
    if kind == "xorshift32":
        state = 0x6D2B79F5
        output = bytearray()
        while len(output) < length:
            state ^= (state << 13) & 0xFFFFFFFF
            state ^= state >> 17
            state ^= (state << 5) & 0xFFFFFFFF
            output.extend(int(state & 0xFFFFFFFF).to_bytes(4, "little"))
        return bytes(output[:length])
    raise ValueError(f"unsupported pattern {kind!r}")


def channel_flag(channel: Any, name: str, default: bool = False) -> bool:
    try:
        return bool(getattr(channel, name))
    except Exception:
        return default


def wait_channels(send: Any, receive: Any, timeout: float) -> tuple[bool, bool, bool]:
    deadline = time.monotonic() + timeout
    send_done = receive_done = False
    while time.monotonic() < deadline:
        send_done = channel_flag(send, "idle")
        receive_done = channel_flag(receive, "idle")
        if send_done and receive_done:
            return True, True, False
        time.sleep(0.0005)
    return send_done, receive_done, True


def status_words(dma: Any, offsets: dict[str, Any]) -> dict[str, int]:
    mmio = getattr(dma, "mmio", None)
    if mmio is None:
        return {}
    values: dict[str, int] = {}
    for name, offset in offsets.items():
        if isinstance(offset, int) and offset >= 0:
            values[name] = int(mmio.read(offset))
    return values


def free_buffer(buffer: Any) -> None:
    for method in ("freebuffer", "close"):
        function = getattr(buffer, method, None)
        if callable(function):
            function()
            return


def buffer_address(buffer: Any) -> int:
    for name in ("device_address", "physical_address"):
        value = getattr(buffer, name, None)
        if isinstance(value, int):
            return value
    raise RuntimeError("allocated PYNQ buffer does not expose a device/physical address")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--download", action="store_true", help="authorize loading the declared Overlay")
    parser.add_argument("--supplemental-evidence", type=Path, help="JSON containing timing/resources source evidence")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    profile_path = args.profile.resolve()
    preflight, preflight_code = validate(profile_path, None, "offline")
    if preflight_code:
        raise SystemExit("offline profile validation failed; resolve errors before board access")
    if not args.download:
        raise SystemExit("board probe requires explicit --download after the admission gate")
    profile = read_json(profile_path)
    overlay_cfg = profile["overlay"]
    board_cfg = profile["board"]
    bit_path = resolve(profile_path, overlay_cfg["bit"], type("Sink", (), {"error": lambda *x: None, "warn": lambda *x: None})(), "overlay.bit")
    hwh_path = resolve(profile_path, overlay_cfg["hwh"], type("Sink", (), {"error": lambda *x: None, "warn": lambda *x: None})(), "overlay.hwh")
    assert bit_path is not None and hwh_path is not None

    model = read_device_tree("model")
    compatible = read_device_tree("compatible")
    missing_tokens = [token for token in board_cfg["compatibility_contains"] if token not in compatible and token not in model]
    if missing_tokens:
        raise SystemExit(f"board compatibility tokens not observed: {missing_tokens}")

    try:
        import numpy as np
        import pynq
        from pynq import MMIO, Overlay, allocate
    except ImportError as exc:
        raise SystemExit(f"pynq_probe.py must run in a PYNQ Python environment: {exc}") from exc

    overlay = Overlay(str(bit_path), download=False)
    for required in overlay_cfg["required_ip"]:
        find_key(overlay.ip_dict, required)
    overlay.download()
    interrupt_inventory = sorted(str(name) for name in getattr(overlay, "interrupt_pins", {}).keys())

    register_cfg = profile["register_contract"]
    register_key = find_key(overlay.ip_dict, register_cfg["ip_name"])
    register_ip = overlay.ip_dict[register_key]
    mmio = MMIO(int(register_ip["phys_addr"]), int(register_ip.get("addr_range", register_cfg["address_span_bytes"])))
    register_by_name = {item["name"]: item for item in register_cfg["registers"]}
    register_reads: dict[str, int] = {}
    identity_mismatches: list[str] = []
    for identity in register_cfg["identity"]:
        register = register_by_name[identity["register"]]
        register_reads[register["name"]] = int(mmio.read(register["offset"]))
        mask = int(identity.get("mask", 0xFFFFFFFF))
        if (register_reads[register["name"]] & mask) != (int(identity["expected"]) & mask):
            identity_mismatches.append(register["name"])

    if identity_mismatches:
        evidence = {
            "evidence_level": "hardware",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "profile_id": profile["profile_id"],
            "board_observation": {"model": model, "compatible": compatible},
            "environment": {"python": sys.version, "platform": platform.platform(), "pynq": getattr(pynq, "__version__", "unknown")},
            "overlay_downloaded": True,
            "artifact_hashes": {"bit": sha256(bit_path), "hwh": sha256(hwh_path)},
            "interrupt_inventory": interrupt_inventory,
            "register_reads": register_reads,
            "identity_mismatches": identity_mismatches,
            "dma_runs": [],
            "performance": {"minimum_throughput_bytes_per_second": 0.0, "maximum_latency_seconds": 0.0, "source": "DMA not started after identity mismatch"},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 1

    dma_cfg = profile["dma_contract"]
    dma_key = find_key(overlay.ip_dict, dma_cfg["ip_name"])
    dma = resolve_attr(overlay, dma_key)
    send = resolve_attr(dma, dma_cfg["mm2s_channel"])
    receive = resolve_attr(dma, dma_cfg["s2mm_channel"])
    dma_runs: list[dict[str, Any]] = []
    timed_out_any = False

    for test in profile["self_tests"]:
        length = int(test["length_bytes"])
        tx = allocate(shape=(length,), dtype=np.uint8)
        rx = allocate(shape=(length,), dtype=np.uint8)
        keep_buffers = False
        transfer_started = False
        start: float | None = None
        cache_operations: list[str] = []
        try:
            source = pattern_bytes(test["pattern"], length)
            tx[:] = np.frombuffer(source, dtype=np.uint8)
            rx[:] = 0
            tx_address = buffer_address(tx)
            rx_address = buffer_address(rx)
            alignment = int(dma_cfg["buffer_alignment_bytes"])
            if tx_address % alignment or rx_address % alignment:
                raise RuntimeError(
                    f"allocated buffer address violates {alignment}-byte alignment: "
                    f"tx=0x{tx_address:x}, rx=0x{rx_address:x}"
                )
            if dma_cfg["cache_policy"]["tx"] == "flush":
                tx.flush()
                cache_operations.append("tx.flush")
            start = time.monotonic()
            receive.transfer(rx)
            send.transfer(tx)
            transfer_started = True
            mm2s_completed, s2mm_completed, timed_out = wait_channels(send, receive, float(test["timeout_seconds"]))
            elapsed = time.monotonic() - start
            statuses = status_words(dma, dma_cfg.get("status_offsets", {}))
            if not timed_out and dma_cfg["cache_policy"]["rx"] == "invalidate":
                rx.invalidate()
                cache_operations.append("rx.invalidate")
            if timed_out:
                output = b""
                mismatch_count = None
                first_mismatch = None
                keep_buffers = True
                timed_out_any = True
            else:
                output = bytes(rx)
                mismatch_indexes = [index for index, pair in enumerate(zip(source, output)) if pair[0] != pair[1]]
                mismatch_count = len(mismatch_indexes)
                first_mismatch = mismatch_indexes[0] if mismatch_indexes else None
            dma_error = channel_flag(send, "error") or channel_flag(receive, "error")
            dma_runs.append({
                "id": test["id"],
                "length_bytes": length,
                "pattern": test["pattern"],
                "tx_device_address": tx_address,
                "rx_device_address": rx_address,
                "elapsed_seconds": elapsed,
                "throughput_bytes_per_second": 0.0 if elapsed <= 0 else length / elapsed,
                "mm2s_completed": mm2s_completed,
                "s2mm_completed": s2mm_completed,
                "tlast_observed": bool(s2mm_completed),
                "tlast_evidence": "S2MM transaction completion",
                "timed_out": timed_out,
                "dma_error": dma_error,
                "dma_status_words": statuses,
                "cache_operations": cache_operations,
                "input_sha256": hashlib.sha256(source).hexdigest(),
                "output_sha256": hashlib.sha256(output).hexdigest() if output else None,
                "mismatch_count": mismatch_count,
                "first_mismatch": first_mismatch,
            })
        except Exception as exc:
            keep_buffers = transfer_started
            timed_out_any = True
            dma_runs.append({
                "id": test["id"],
                "length_bytes": length,
                "pattern": test["pattern"],
                "elapsed_seconds": time.monotonic() - start if start is not None else 0.0,
                "throughput_bytes_per_second": 0.0,
                "mm2s_completed": False,
                "s2mm_completed": False,
                "tlast_observed": False,
                "timed_out": False,
                "dma_error": True,
                "error_message": f"{type(exc).__name__}: {exc}",
                "dma_status_words": status_words(dma, dma_cfg.get("status_offsets", {})),
                "cache_operations": cache_operations,
                "mismatch_count": None,
                "first_mismatch": None,
            })
        finally:
            if not keep_buffers:
                free_buffer(tx)
                free_buffer(rx)
        if timed_out_any:
            break

    throughputs = [item["throughput_bytes_per_second"] for item in dma_runs if not item["timed_out"]]
    latencies = [item["elapsed_seconds"] for item in dma_runs]
    evidence: dict[str, Any] = {
        "evidence_level": "hardware",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_id": profile["profile_id"],
        "board_observation": {"model": model, "compatible": compatible},
        "environment": {"python": sys.version, "platform": platform.platform(), "pynq": getattr(pynq, "__version__", "unknown")},
        "overlay_downloaded": True,
        "artifact_hashes": {"bit": sha256(bit_path), "hwh": sha256(hwh_path)},
        "interrupt_inventory": interrupt_inventory,
        "register_reads": register_reads,
        "dma_runs": dma_runs,
        "performance": {
            "minimum_throughput_bytes_per_second": min(throughputs) if throughputs else 0.0,
            "maximum_latency_seconds": max(latencies) if latencies else float("inf"),
            "source": "pynq_probe.py monotonic measurements"
        },
    }
    if args.supplemental_evidence:
        supplemental = read_json(args.supplemental_evidence.resolve())
        for key in ("timing", "resources"):
            if key in supplemental:
                evidence[key] = supplemental[key]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 1 if timed_out_any or any(item["dma_error"] or item["mismatch_count"] not in (0, None) for item in dma_runs) else 0


if __name__ == "__main__":
    sys.exit(main())
