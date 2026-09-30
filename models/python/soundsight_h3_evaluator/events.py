"""Source-frame identity, native event partial order and sealed outcome classification."""

from __future__ import annotations

import hashlib
import json

from .bundle import BundleError, IdentityError, require, uint

STREAMS = ("frame", "status", "commit", "take", "cancel", "late_error")
EVENT_KINDS = {"STATUS", "NUMERIC", "AVAILABLE", "COMMIT", "TAKE", "CANCEL",
               "FATAL", "STOP", "REVOKE", "LATE_ERROR", "DECISION", "NOTICE"}
EXPECTED_UNITS = tuple(
    ["transport", "frame_domain", "binding"] +
    [name for ch in range(4) for name in (f"mean_{ch}", f"gate_window_{ch}", f"doa_window_{ch}")] +
    [name for domain in ("gate", "doa") for ch in range(4)
     for name in (f"{domain}_fft_{ch}", f"{domain}_fixed4_{ch}")] +
    ["gate_state"] +
    [name for pair in ("01", "02", "03", "12", "13", "23")
     for name in (f"phat_{pair}", f"ifft_{pair}", f"lag_{pair}")] +
    ["doa", "tracker", "result_binding"])


def key_for_window(run: dict, window: dict) -> dict | None:
    c = run["capture"]
    fields = ("boot_id", "session_id", "interval_id", "algorithm_id", "config_id",
              "calibration_id", "generation", "epoch")
    if any(isinstance(c.get(field), dict) for field in fields):
        return None
    return {"run_id": run["run_id"], "boot_id": c["boot_id"],
            "session_id": c["session_id"], "interval_id": c["interval_id"],
            "epoch": c["epoch"], "frame_index": window["frame_index"],
            "start_original_id": window["start_original_id"],
            "last_original_id": window["last_original_id"],
            "generation": c["generation"], "algorithm_id": c["algorithm_id"],
            "config_id": c["config_id"], "calibration_id": c["calibration_id"]}


def key_digest(key: dict) -> str:
    raw = json.dumps(key, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _event_at(event: dict) -> dict:
    at = event.get("at")
    require(isinstance(at, dict), f"EVENT_AT_REQUIRED:{event.get('event_id')}")
    require(isinstance(at.get("domain"), str) and at["domain"], "EVENT_CLOCK_DOMAIN_REQUIRED")
    uint(at.get("epoch"), "event.epoch")
    uint(at.get("tick"), "event.tick")
    if "seq" in at and at["seq"] is not None:
        uint(at["seq"], "event.seq")
    if "edge_id" in at and at["edge_id"] is not None:
        require(isinstance(at["edge_id"], str) and at["edge_id"], "EVENT_EDGE_ID")
    return at


def prepare_events(run: dict) -> tuple[dict[str, dict], dict[str, set[str]], list[dict]]:
    events: dict[str, dict] = {}
    issues: list[dict] = []
    event_rows = run["algorithm"]["events"]
    for event in event_rows if isinstance(event_rows, list) else []:
        require(isinstance(event, dict), "EVENT_NOT_OBJECT")
        eid = event.get("event_id")
        require(isinstance(eid, str) and eid, "EVENT_ID_REQUIRED")
        require(isinstance(event.get("kind"), str) and event["kind"] in EVENT_KINDS,
                f"EVENT_KIND_INVALID:{eid}")
        _event_at(event)
        if eid in events:
            if event == events[eid] and event["kind"] == "NOTICE" and event.get("no_side_effect") is True:
                continue
            issues.append({"kind": "DUPLICATE_OR_CONFLICTING_EVENT_ID", "event_id": eid,
                           "first": events[eid], "other": event})
            continue
        events[eid] = event
    edges: dict[str, set[str]] = {eid: set() for eid in events}
    order_edges = run["time_proof"].get("order_edges", [])
    require(isinstance(order_edges, list), "ORDER_EDGES_LIST_REQUIRED")
    for edge in order_edges:
        require(isinstance(edge, list) and len(edge) == 2 and
                all(isinstance(part, str) for part in edge), "ORDER_EDGE_PAIR_REQUIRED")
        a, b = edge
        require(a in events and b in events and a != b, f"ORDER_EDGE_UNKNOWN:{a}:{b}")
        edges[a].add(b)
    for eid, event in events.items():
        causes = event.get("causes", [])
        require(isinstance(causes, list) and all(isinstance(x, str) for x in causes),
                f"CAUSES_LIST_REQUIRED:{eid}")
        for earlier in causes:
            require(earlier in events and earlier != eid, f"CAUSE_UNKNOWN:{eid}:{earlier}")
            edges[earlier].add(eid)
    for earlier, later_set in edges.items():
        a = events[earlier]["at"]
        for later in later_set:
            b = events[later]["at"]
            if a["domain"] == b["domain"] and a["epoch"] == b["epoch"] and a["tick"] > b["tick"]:
                raise IdentityError(f"CAUSAL_EDGE_CONTRADICTS_NATIVE_CLOCK:{earlier}:{later}")
    # A contradictory proof is an identity conflict, never an ordering hint.
    visiting, visited = set(), set()

    def visit(node: str) -> None:
        if node in visiting:
            raise BundleError(f"ORDER_CYCLE:{node}")
        if node in visited:
            return
        visiting.add(node)
        for child in edges[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for eid in events:
        visit(eid)
    return events, edges, issues


def _reaches(edges: dict[str, set[str]], a: str, b: str) -> bool:
    todo, seen = list(edges[a]), set()
    while todo:
        node = todo.pop()
        if node == b:
            return True
        if node not in seen:
            seen.add(node)
            todo.extend(edges[node])
    return False


def relation(a: dict, b: dict, edges: dict[str, set[str]]) -> str:
    """Return BEFORE, AFTER, SAME_EDGE or UNKNOWN; no log-line-order inference."""
    if a["event_id"] == b["event_id"]:
        return "SAME_EDGE"
    if _reaches(edges, a["event_id"], b["event_id"]):
        return "BEFORE"
    if _reaches(edges, b["event_id"], a["event_id"]):
        return "AFTER"
    ta, tb = a["at"], b["at"]
    if ta["domain"] != tb["domain"] or ta["epoch"] != tb["epoch"]:
        return "UNKNOWN"
    if ta["tick"] < tb["tick"]:
        return "BEFORE"
    if ta["tick"] > tb["tick"]:
        return "AFTER"
    if ta.get("edge_id") and ta.get("edge_id") == tb.get("edge_id"):
        return "SAME_EDGE"
    sa, sb = ta.get("seq"), tb.get("seq")
    if sa is not None and sb is not None:
        return "BEFORE" if sa < sb else "AFTER" if sa > sb else "UNKNOWN"
    return "UNKNOWN"


def _watermark_index(run: dict) -> dict[str, dict]:
    by_name = {}
    stream_rows = run["watermarks"]["streams"]
    for stream in stream_rows if isinstance(stream_rows, list) else []:
        require(isinstance(stream, dict), "WATERMARK_NOT_OBJECT")
        name = stream.get("name")
        require(isinstance(name, str) and name not in by_name, "WATERMARK_DUPLICATE_OR_NAME")
        keys = stream.get("terminal_keys", [])
        require(isinstance(keys, list), "WATERMARK_TERMINAL_KEYS_LIST")
        require(all(isinstance(k, str) and len(k) == 64 and
                    all(ch in "0123456789abcdef" for ch in k) for k in keys),
                "WATERMARK_TERMINAL_KEY_INVALID")
        by_name[name] = {**stream, "terminal_keys": set(keys)}
    return by_name


def _all_terminal(by_name: dict[str, dict], kid: str, expiry: int | None) -> bool:
    if expiry is None:
        return False
    for name in STREAMS:
        item = by_name.get(name)
        if not item or item.get("sealed") is not True or item.get("continuous") is not True or (
                item.get("lost_count") != 0 or item.get("flush_ack") is not True or
                kid not in item.get("terminal_keys", []) or
                type(item.get("source_epoch")) is not int or
                type(item.get("first_seq")) is not int or
                type(item.get("last_seq")) is not int or
                item["first_seq"] > item["last_seq"] or
                type(item.get("through_original_id")) is not int or
                item["through_original_id"] < expiry):
            return False
    return True


def _expiry(run: dict, window: dict) -> tuple[int | None, str | None]:
    ttl = run["time_proof"].get("T_result")
    if not isinstance(ttl, dict) or ttl.get("unit") != "original_samples" or type(ttl.get("value")) is not int:
        return None, "T_RESULT_MISSING_OR_UNIT_UNKNOWN"
    value = uint(ttl["value"], "T_result")
    last = window["last_original_id"]
    if value > (1 << 64) - 1 - last:
        return None, "T_RESULT_OVERFLOW"
    return last + value, None


def _original_interval(event: dict, label: str) -> tuple[int, int] | None:
    interval = event.get("original_id_interval")
    if not isinstance(interval, list) or len(interval) != 2:
        return None
    lo, hi = (uint(interval[i], f"{label}.original_id_interval.{i}") for i in (0, 1))
    require(lo <= hi, f"{label}.ORIGINAL_INTERVAL_REVERSED")
    return lo, hi


def _time_qualified(run: dict, formal: bool, expiry: int | None,
                    verified_ref_ids: set[str]) -> bool:
    proof = run["time_proof"]
    if not formal and proof.get("basis") == "SYNTHETIC_TIME":
        return True
    if proof.get("basis") != "REAL_OBSERVED" or expiry is None:
        return False
    ttl = proof.get("T_result")
    if not (isinstance(ttl, dict) and ttl.get("status") == "FROZEN" and
            isinstance(ttl.get("policy_ref"), str) and ttl["policy_ref"] in verified_ref_ids and
            isinstance(proof.get("consumer_id"), str) and proof["consumer_id"] and
            isinstance(proof.get("consumer_source_ref"), str) and
            proof["consumer_source_ref"] in verified_ref_ids and
            proof.get("anchor_status") == "SEALED"):
        return False
    anchors = proof.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        return False
    first = run["capture"]["first_original_id"]
    if type(first) is not int:
        return False
    for anchor in anchors:
        if not isinstance(anchor, dict) or not isinstance(anchor.get("source_ref"), str) or anchor["source_ref"] not in verified_ref_ids:
            continue
        if not isinstance(anchor.get("native_domain"), str) or not anchor["native_domain"]:
            continue
        if any(type(anchor.get(name)) is not int or anchor[name] < 0 for name in
               ("native_epoch", "native_tick", "source_original_id", "error_before_samples",
                "error_after_samples", "covers_first_original_id", "covers_through_original_id")):
            continue
        if anchor["covers_first_original_id"] <= first and anchor["covers_through_original_id"] >= expiry:
            return True
    return False


def classify_result(run: dict, window: dict, key: dict | None, events: dict[str, dict],
                    edges: dict[str, set[str]], formal: bool,
                    related: list[dict], watermarks: dict[str, dict],
                    verified_ref_ids: set[str]) -> dict:
    kid = key_digest(key) if key is not None else None
    ids = [e["event_id"] for e in related]
    outcome = {"key": key, "key_sha256": kid, "class": "UNRESOLVED", "reason": None,
               "event_ids": ids, "first_take_event_id": None, "take_history": [],
               "angle_deg": None, "expiry_original_id": None, "failure_flags": []}

    def done(cls: str, reason: str, *flags: str) -> dict:
        outcome.update({"class": cls, "reason": reason})
        outcome["failure_flags"].extend(flags)
        return outcome

    if key is None:
        return done("UNRESOLVED", "SOURCE_FRAME_IDENTITY_MISSING")
    if not isinstance(run["algorithm"]["events"], list):
        return done("UNRESOLVED", "ALGORITHM_EVENT_SOURCE_MISSING")
    take = [e for e in related if e["kind"] == "TAKE" and e.get("result") == "SUCCESS"]
    outcome["take_history"] = [e["event_id"] for e in take]
    if len(take) == 1:
        outcome["first_take_event_id"] = take[0]["event_id"]
    if len(take) > 1:
        return done("DETERMINATE_NONFRESH", "DUPLICATE_SUCCESSFUL_TAKE", "PROTOCOL_FAIL")
    numeric = [e for e in related if e["kind"] == "NUMERIC"]
    if any(e.get("result") == "INVALID" for e in numeric):
        return done("DETERMINATE_NONFRESH", "NUMERIC_INVALID", "NUMERIC_FAIL")
    units = run["algorithm"]["required_units"]
    status = [e for e in related if e["kind"] == "STATUS"]
    if isinstance(units, list) and units:
        early_status = [e for e in status if e.get("unit") in units and e.get("result") == "ERROR"]
        if early_status:
            return done("DETERMINATE_NONFRESH", "REQUIRED_STATUS_ERROR", "NUMERIC_OR_PROTOCOL_FAIL")
    if any(e["kind"] in {"LATE_ERROR", "REVOKE"} and e.get("invalidates_result") is True
           for e in related):
        return done("DETERMINATE_NONFRESH", "INVALIDATING_ERROR_OBSERVED", "PROTOCOL_OR_NUMERIC_FAIL")
    expiry, expiry_error = _expiry(run, window)
    outcome["expiry_original_id"] = expiry
    if expiry_error == "T_RESULT_OVERFLOW":
        return done("DETERMINATE_NONFRESH", expiry_error, "TIME_CONTRACT_FAIL")
    terminal = _all_terminal(watermarks, kid, expiry) and all(
        watermarks[name]["source_epoch"] == run["capture"]["epoch"] for name in STREAMS)
    if not _time_qualified(run, formal, expiry, verified_ref_ids):
        return done("UNRESOLVED", "REAL_TIME_ANCHOR_OR_CONSUMER_MISSING")
    if expiry is None:
        return done("UNRESOLVED", expiry_error or "EXPIRY_UNRESOLVED")
    if len(numeric) != 1 or numeric[0].get("result") != "VALID":
        return done("DETERMINATE_NONFRESH" if terminal else "UNRESOLVED",
                    "NUMERIC_QUALIFICATION_MISSING_OR_DUPLICATE" if terminal else
                    "NUMERIC_QUALIFICATION_UNSEALED", *("PROTOCOL_FAIL",) if terminal else ())
    if not isinstance(units, list) or not units or len(units) != len(set(units)):
        return done("UNRESOLVED", "REQUIRED_UNIT_SET_MISSING_OR_DUPLICATE")
    by_unit = {u: [e for e in status if e.get("unit") == u] for u in units}
    if any(len(v) > 1 for v in by_unit.values()):
        return done("DETERMINATE_NONFRESH", "DUPLICATE_REQUIRED_STATUS", "PROTOCOL_FAIL")
    if any(not v for v in by_unit.values()):
        return done("DETERMINATE_NONFRESH" if terminal else "UNRESOLVED",
                    "REQUIRED_STATUS_MISSING_CONFIRMED" if terminal else "REQUIRED_STATUS_MISSING",
                    *("PROTOCOL_FAIL",) if terminal else ())
    if any(v[0].get("result") not in {"OK", "SKIPPED"} or
           (v[0].get("result") == "SKIPPED" and not v[0].get("branch_reason"))
           for v in by_unit.values()):
        return done("UNRESOLVED", "REQUIRED_STATUS_NOT_VALIDATED")
    if not take:
        reject = [e for e in related if e["kind"] == "DECISION" and e.get("result") in {"HOLD", "REJECTED"}]
        return done("DETERMINATE_NONFRESH" if terminal else "UNRESOLVED",
                    (reject[0]["result"] if reject else "NO_RESULT") if terminal else
                    "TAKE_ABSENCE_NOT_SEALED")
    one = take[0]
    consumer = run["time_proof"].get("consumer_id")
    if not isinstance(consumer, str) or not consumer:
        return done("UNRESOLVED", "DESIGNATED_CONSUMER_MISSING")
    if one.get("consumer_id") != consumer:
        return done("DETERMINATE_NONFRESH", "WRONG_CONSUMER_SUCCESSFUL_TAKE", "PROTOCOL_FAIL")
    if one.get("delivery") != "FRESH":
        return done("DETERMINATE_NONFRESH" if terminal else "UNRESOLVED",
                    "TAKEN_NO_FRESH" if terminal else "TAKE_QUALIFICATION_UNSEALED")
    interval = _original_interval(one, "take")
    if interval is None:
        return done("UNRESOLVED", "TAKE_ORIGINAL_ID_ANCHOR_MISSING")
    lo, hi = interval
    if lo > expiry:
        return done("DETERMINATE_NONFRESH", "TAKE_EXPIRED", "PROTOCOL_FAIL")
    if hi > expiry:
        return done("UNRESOLVED", "TAKE_EXPIRY_INTERVAL_CROSSES_BOUNDARY")
    available = [e for e in related if e["kind"] == "AVAILABLE"]
    commit = [e for e in related if e["kind"] == "COMMIT" and e.get("result") == "SUCCESS"]
    if len(available) != 1 or len(commit) != 1:
        return done("DETERMINATE_NONFRESH" if terminal else "UNRESOLVED",
                    "AVAILABLE_OR_COMMIT_MISSING_OR_DUPLICATE",
                    *("PROTOCOL_FAIL",) if terminal else ())
    available_interval = _original_interval(available[0], "available")
    if available_interval is None:
        return done("UNRESOLVED", "AVAILABLE_ORIGINAL_ID_ANCHOR_MISSING")
    if available_interval[1] < window["last_original_id"]:
        return done("DETERMINATE_NONFRESH", "AVAILABLE_BEFORE_SOURCE_FRAME_END", "PROTOCOL_FAIL")
    if available_interval[0] < window["last_original_id"]:
        return done("UNRESOLVED", "AVAILABLE_FRAME_END_INTERVAL_CROSSES_BOUNDARY")
    for earlier, later in ([(v[0], available[0]) for v in by_unit.values()] +
                           [(numeric[0], available[0])] +
                           [(available[0], commit[0]), (commit[0], one)]):
        rel = relation(earlier, later, edges)
        if rel == "AFTER":
            return done("DETERMINATE_NONFRESH", "CAUSAL_ORDER_VIOLATION", "PROTOCOL_FAIL")
        if rel in {"UNKNOWN", "SAME_EDGE"}:
            return done("UNRESOLVED", "CAUSAL_ORDER_UNPROVEN")
    for cancel in (e for e in related if e["kind"] in {"CANCEL", "FATAL"}):
        rel = relation(cancel, one, edges)
        if rel in {"BEFORE", "SAME_EDGE"}:
            return done("DETERMINATE_NONFRESH", "CANCEL_PRECEDES_OR_SAME_EDGE_TAKE")
        if rel == "UNKNOWN":
            return done("UNRESOLVED", "CANCEL_TAKE_ORDER_UNPROVEN")
    if not terminal:
        return done("UNRESOLVED", "TERMINAL_WATERMARK_INCOMPLETE")
    if one.get("angle_deg") is None:
        return done("DETERMINATE_NONFRESH", "FRESH_ANGLE_MISSING", "PROTOCOL_FAIL")
    outcome["angle_deg"] = one["angle_deg"]
    return done("VALID_FRESH", "FIRST_SUCCESSFUL_TAKE_SEALED")


def resolve_events(run: dict, windows: list[dict], formal: bool,
                   verified_ref_ids: set[str]) -> tuple[dict[int, dict], list[dict]]:
    events, edges, issues = prepare_events(run)
    watermarks = _watermark_index(run)
    keys = {w["frame_index"]: key_for_window(run, w) for w in windows}
    known = {key_digest(k) for k in keys.values() if k is not None}
    by_key: dict[str, list[dict]] = {}
    for event in events.values():
        key = event.get("key")
        if event["kind"] == "NOTICE":
            continue
        if not isinstance(key, dict):
            issues.append({"kind": "EVENT_KEY_MISSING", "event_id": event["event_id"], "event": event})
        elif key_digest(key) not in known:
            issues.append({"kind": "UNKNOWN_K", "event_id": event["event_id"], "event": event})
        else:
            by_key.setdefault(key_digest(key), []).append(event)
    outcomes = {w["frame_index"]: classify_result(run, w, keys[w["frame_index"]], events, edges,
                formal, by_key.get(key_digest(keys[w["frame_index"]]), []) if keys[w["frame_index"]] else [],
                watermarks, verified_ref_ids)
                for w in windows}
    return outcomes, issues
