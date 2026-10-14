"""Logical offline commands; output always reports scope and failures."""
import argparse
import json
from pathlib import Path
import sys
from .contracts import (Profile, ProtocolError, Refusal, file_identity,
                        hardware_admission, inspect_artifacts, keys, read_json, require)
from .dma_rx import TestTransport
from .evidence import Evidence
from .records import decode_raw
from .session import Session


def parser():
    root = argparse.ArgumentParser(prog="python -m soundsight_ps")
    commands = root.add_subparsers(dest="command", required=True)
    for command in ("inspect", "decode", "replay", "hardware"):
        sub = commands.add_parser(command)
        sub.add_argument("--out", required=True, help="new exclusive evidence directory")
        if command != "hardware":
            sub.add_argument("--profile", required=True)
            sub.add_argument("--artifact-root", required=True)
        if command == "decode":
            sub.add_argument("--raw", required=True)
        if command == "replay":
            sub.add_argument("--script", required=True)
    return root


def replay(profile, script, evidence):
    transport = TestTransport(script)
    session = Session(profile, transport, evidence)
    failures = []
    internal_failure = False
    try:
        for action in transport.actions:
            keys(action, ("op",), ("slot", "authorized"))
            op = action["op"]
            require(op in {"start", "submit", "complete", "native", "stop", "restart", "abort", "close"},
                    "unsupported action")
            if session.first_error is not None:
                require(op in {"abort", "close"}, "only explicit abort/close permitted after failure")
            try:
                if op == "submit":
                    keys(action, ("op", "slot"))
                    session.submit(action["slot"])
                elif op == "abort":
                    keys(action, ("op", "authorized"))
                    session.abort(action["authorized"])
                else:
                    keys(action, ("op",))
                    method = session.consume_native if op == "native" else getattr(session, op)
                    method()
            except (ProtocolError, KeyboardInterrupt) as exc:
                failures.append({"action": op, "type": type(exc).__name__, "message": str(exc)})
        require(transport.exhausted(), "unused transcript observations")
        require(session.state == "CLOSED", "transcript ended with unclosed/pinned ownership")
    except BaseException as exc:
        session._failed(exc)
        failures.append({"action": "replay", "type": type(exc).__name__, "message": str(exc)})
        if not isinstance(exc, (ProtocolError, KeyboardInterrupt)):
            internal_failure = True
    return {"session": session.summary(), "failures": failures,
            "events_consumed": transport.index, "events_total": len(transport.events)}, 4 if internal_failure else (2 if failures else 0)


def main(argv=None):
    args = parser().parse_args(argv)
    evidence = None
    identities = {}
    result = {"command": args.command, "scope": "OFFLINE_SOFTWARE_ONLY", "hardware": "NOT_RUN",
              "acceptance": "NOT_CLAIMED", "ps_time_bound": "UNKNOWN"}
    code = 0
    try:
        evidence = Evidence(args.out)
        if args.command == "hardware":
            hardware_admission()
        for attr in ("profile", "script", "raw"):
            if hasattr(args, attr):
                path = Path(getattr(args, attr)).absolute()
                actual = file_identity(path)
                identities[actual["path"]] = actual
        profile = Profile.parse(read_json(args.profile))
        artifact_report = inspect_artifacts(args.artifact_root, profile.data["artifacts"])
        for artifact in artifact_report["artifacts"]:
            actual = artifact["actual"]
            identities[actual["path"]] = actual
        evidence.event("inputs_before", identities=list(identities.values()))
        result["artifacts"] = artifact_report
        if args.command == "inspect":
            result["profile"] = profile.data
            result["runtime_admission"] = "UNBOUND"
        elif args.command == "decode":
            raw = Path(args.raw).read_bytes()
            archive = evidence.snapshot("raw", raw, {"scope": "OFFLINE_INPUT", "raw_schema": "raw32-le-s24-v1",
                     "boot": profile.data["boot"], "epoch": profile.data["epoch"],
                     "generation": profile.data["generation"], "source_input": identities[str(Path(args.raw).resolve())]})
            frames = decode_raw(raw)
            for previous, current in zip(frames, frames[1:]):
                require(current.source_id > previous.source_id, "duplicate/backwards source ID")
                if current.source_id != previous.source_id + 1:
                    evidence.event("source_id_gap", previous=previous.source_id, current=current.source_id,
                                   drop_semantics="UNKNOWN")
            evidence.snapshot("integer-export", json.dumps([f.as_dict() for f in frames], sort_keys=True).encode("utf-8"),
                              {"raw_file": archive["raw_file"], "normalization": "NONE", "clip_is_drop": False})
            result["frames"] = len(frames)
        else:
            output, code = replay(profile, read_json(args.script), evidence)
            result.update(output)
    except Refusal as exc:
        code = 3
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    except (ProtocolError, ValueError, FileNotFoundError, KeyboardInterrupt) as exc:
        code = 2
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    except BaseException as exc:
        code = 4
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    # 中文用途：无论结果如何都核输入前后身份；此处只保存证据，不执行硬件清理。
    try:
        after = [file_identity(path) for path in identities]
        result["input_identities_before"] = list(identities.values())
        result["input_identities_after"] = after
        require(result["input_identities_before"] == after, "read-only input identity changed")
    except BaseException as exc:
        code = 2
        result["input_identity_error"] = str(exc)
    result["exit_code"] = code
    if evidence is not None:
        try:
            evidence.report(result)
        except BaseException as exc:
            code = 4
            result["exit_code"] = code
            result["evidence_error"] = str(exc)
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
