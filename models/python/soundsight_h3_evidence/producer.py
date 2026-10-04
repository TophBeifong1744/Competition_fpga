"""Saved fields/links only. Does not import algorithms or evaluate lag mathematics."""
import json

from .contracts import (Issue, Resource, ROLES, RULE_HASHES, SPEC, RAW, PROFILE,
                        PAIRS, UnconsumedNumber, binding, bounded_json, known, unknown, uint)
from .sources import npy_layout, zip_directory


def json_value(x):
    """New report representation, not re-encoding the identity of original bytes."""
    if type(x) is int:
        return str(x)
    if isinstance(x, UnconsumedNumber):
        return {"source_numeric_token": str(x), "interpreted": False}
    if type(x) is list:
        return [json_value(v) for v in x]
    if type(x) is dict:
        return {k: json_value(v) for k, v in x.items()}
    return x


def raw_error(source_id, locator, reason, category="UNKNOWN", status=None, positions=None):
    """Retain original strings at the source; never manufacture a typed Error."""
    n = len(reason.encode("utf-8")) if type(reason) is str else None
    issues = []
    if n is not None and n > 64:
        issues.append("WOULD_EXCEED_ERROR_REASON_64_UTF8_BYTES")
    if n is not None and n > 1024:
        issues.append("RAW_TEXT_1024_BYTES_EXCEEDED_USE_ORIGINAL_SOURCE")
    return {"source_id": source_id, "locator": locator, "category": category,
            "original_status": known(json_value(status)) if status is not None else unknown("No status saved at this reason locator"),
            "raw_reason": known(reason) if n is not None and n <= 1024 else unknown("See complete original source bytes at locator"),
            "reason_utf8_bytes": str(n) if n is not None else unknown("Original reason is not a recorded UTF8 string"),
            "raw_reason_source": {"source_id": source_id, "locator": locator},
            "positions": json_value(positions) if positions is not None else unknown("Not recorded"),
            "typed_error_ref": unknown("Original typed namespace/code/native/Admission not supplied"),
            "representation_issues": issues}


def error_capacity(errors):
    return ["WOULD_EXCEED_EIGHT_ERROR_SLOTS_NO_TRUNCATION"] if len(errors) > 8 else []


class Producer:
    def __init__(self, am, selection, registry, store):
        self.am, self.selection, self.registry, self.store = am, selection, registry, store
        self.conflicts, self.missing, self.unsupported = [], [], []
        self.original_errors, self.views = [], []
        self.consumed = []
        self.roles, self.unavailable = {}, set()
        self.histories = []
        self.support_views = []

    def note(self, axis, reason, sid=None, view=None, details=None, locator=""):
        target = getattr(self, axis)
        target.append({"id": f"{axis}-{len(target)}", "view_ids": [view] if view else [],
                       "rule": reason, "source_ids": [sid] if sid else [], "locator": locator,
                       "reason": reason, "evidence_refs": [self.store.entries[sid]["ref"]] if sid else [],
                       "details": json_value(details or {})})

    def dispatch(self, sid):
        e = self.store.entries[sid]
        r = e["ref"]
        schema = {k: v for k, v in r.items() if k != "content_sha256"}
        matches = [x for x in self.registry["entries"] if x["source_schema"] == schema]
        if len(matches) != 1:
            raise Resource("UNSUPPORTED_SOURCE_SCHEMA", {"source_id": sid, "schema": schema})
        reg = matches[0]
        if (r["schema_version"] != "1" or r["schema_sha256"] != SPEC or r["encoding"] != "RAW_BYTES"
                or ROLES.get(r["schema_id"]) != (reg["decoder_role"], reg["scope_rule"])):
            raise Resource("UNSUPPORTED_ROLE_OR_SCOPE", {"source_id": sid})
        if {"sha256": r["content_sha256"], "byte_length": e["byte_length"]} not in reg["whitelist"]:
            raise Resource("SOURCE_NOT_WHITELISTED", {"source_id": sid})
        role = reg["decoder_role"]
        if role == "WHITELIST_RULE_BYTES" and r["content_sha256"] not in RULE_HASHES:
            raise Resource("RULE_SCOPE_NOT_PROVEN", {"source_id": sid})
        return role

    def source(self, sid, view=None):
        if sid in self.unavailable:
            return None
        try:
            role = self.dispatch(sid)
            loc = self.store.entries[sid]["location"]
            if loc["kind"] == "ZIP_MEMBER" and self.source(loc["container_id"], view) is None:
                self.note("missing", "MEMBER_PARENT_NOT_ADMITTED", sid, view)
                self.unavailable.add(sid)
                return None
            b = self.store.get(sid)
            self.roles[sid] = role
            if sid not in self.consumed:
                self.consumed.append(sid)
            return b
        except Resource as e:
            self.note("unsupported", e.reason, sid, view, e.details)
        except Issue as e:
            if e.code in (2, 4):
                raise
            self.note("conflicts" if e.code == 3 else "missing", e.reason, sid, view, e.details)
        self.unavailable.add(sid)
        return None

    def legacy(self, sid, view=None):
        b = self.source(sid, view)
        if b is None:
            return None
        try:
            result = bounded_json(b)
            if type(result) is not dict:
                raise Issue(3, "SOURCE_ROOT_OBJECT_REQUIRED")
            return result
        except Resource as e:
            self.note("unsupported", e.reason, sid, view, e.details)
        except Issue as e:
            self.note("conflicts", e.reason, sid, view, e.details)
        return None

    def run(self):
        # Decode only one legacy source at a time. Selected small report records
        # survive; complete decoded result/config/index trees are never cached.
        needed = []
        for v in self.selection["views"]:
            for sid in [v["result_id"], *v["support_ids"]]:
                if sid not in needed:
                    needed.append(sid)
            if v["array_view"]["state"] == "KNOWN":
                for key in ("container_id", "member_id"):
                    sid = v["array_view"]["value"][key]
                    if sid not in needed:
                        needed.append(sid)
            if v["context_id"]["state"] == "KNOWN":
                sid = v["context_id"]["value"]
                if sid not in needed:
                    needed.append(sid)
        self.required = set(needed)
        for sid in sorted(needed, key=list(self.store.entries).index):
            try:
                role = self.dispatch(sid)
            except Resource:
                self.source(sid)
                continue
            if role == "SAVED_RESULT_FIELDS":
                data = self.legacy(sid)
                for v in self.selection["views"]:
                    if v["result_id"] == sid:
                        self.extract_view(v, data)
                if data is not None:
                    # Full unmodified history is also available in copied original source.
                    for name in ("events", "terminations", "observations", "frames", "status", "eof_stop_audit"):
                        if name in data:
                            self.histories.append({"source_id": sid, "locator": "/" + name,
                                                   "original_source_preserved": True,
                                                   "native_interpretation": "NOT_RUN"})
                del data
            elif role in ("SAVED_RUN_LINKS", "RESEARCH_CONFIG_FIELDS"):
                data = self.legacy(sid)
                if data is not None:
                    self.check_links(sid, role, data)
                del data
            else:
                b = self.source(sid)
                if b is not None and role == "SAVED_MEMBER_LAYOUT":
                    try:
                        npy_layout(b)
                    except Issue as e:
                        self.note("conflicts", e.reason, sid, details=e.details)
        # Unavailable result views must not disappear from the complete selection denominator.
        completed = {v["id"] for v in self.views}
        for v in self.selection["views"]:
            if v["id"] not in completed:
                self.extract_view(v, None)
        self.views.sort(key=lambda v: uint(v["ordinal"]))
        for v in self.selection["views"]:
            self.array_view(v)
            if v["context_id"]["state"] == "UNKNOWN":
                self.note("missing", "MISSING_INDEPENDENT_SOURCE_CONTEXT", view=v["id"])
            else:
                self.source(v["context_id"]["value"], v["id"])
                self.note("unsupported", "NO_NAMED_CONTEXT_CODEC", v["context_id"]["value"], v["id"])
        for role, reason in (("SAVED_RUN_LINKS", "MISSING_RUN_INDEX_LINK"), ("RESEARCH_CONFIG_FIELDS", "MISSING_RESEARCH_CONFIG_LINK")):
            if role not in self.roles.values():
                self.note("missing", reason)
        self.note("missing", "FULL_K_ORDERED_ROOTS_NATIVE_LIFETIME_NOT_OBTAINED")
        unique = {}
        for e in self.original_errors:
            unique.setdefault((e["source_id"], e["locator"]), e)
        self.original_errors = list(unique.values())
        for i, e in enumerate(self.original_errors):
            e["id"] = f"original-error-{i}"
        return self.report()

    def extract_view(self, v, data):
        ordinal = self.selection["views"].index(v)
        sid, j, k = v["result_id"], uint(v["stage_ordinal"]), uint(v["pair_ordinal"], 5)
        out = {"id": v["id"], "ordinal": str(ordinal), "selection": v,
               "processed": False, "facts": [], "partial_identity": {}, "source_ids": [sid],
               "numeric_audit": {}, "saved_status": {}, "association": "INCOMPLETE"}
        self.views.append(out)
        if data is None:
            self.note("missing", "RESULT_FIELDS_NOT_OBTAINED", sid, v["id"])
            return
        try:
            stages = data.get("stage_details")
            if type(stages) is not list or j >= len(stages):
                raise Issue(3, "SOURCE_STAGE_LOCATOR_CONFLICT")
            stage = stages[j]
            detail = stage.get("detail") if type(stage) is dict else None
            if type(detail) is not dict:
                raise Issue(3, "SOURCE_DETAIL_TYPE")
            identity = detail.get("frame_identity")
            if type(identity) is not dict:
                identity = {}
                self.note("missing", "MISSING_PARTIAL_IDENTITY", sid, v["id"])
            for name in ("boot", "session", "interval", "frame", "generation", "last_id"):
                value = identity.get(name)
                if value is None:
                    out["partial_identity"][name] = unknown("Not recorded")
                    continue
                if name in ("boot", "session", "interval"):
                    if type(value) is not str or not 1 <= len(value.encode("utf-8")) <= 64:
                        raise Issue(3, "PARTIAL_IDENTITY_OPAQUE_DOMAIN", {"field": name})
                elif type(value) is not int or not 0 <= value < (1 << 64):
                    raise Issue(3, "PARTIAL_IDENTITY_INTEGER", {"field": name})
                out["partial_identity"][name] = known(json_value(value))
            if "frame" in identity and identity["frame"] != j:
                self.note("conflicts", "SOURCE_WRITER_FRAME_ORDINAL", sid, v["id"], {"ordinal": j, "source_frame": identity["frame"]})
            rows = detail.get("pair_rows")
            if type(rows) is not list or k >= len(rows) or type(rows[k]) is not dict:
                raise Issue(3, "SOURCE_PAIR_LOCATOR_CONFLICT")
            row = rows[k]
            limits = {"peak": (-1024, 1024), "delta_q12": (-2048, 2048), "tau_q12": (-(1 << 31), (1 << 31) - 1),
                      "peak_code": (-(1 << 24), (1 << 24) - 1), "physical_limit_q12": (0, (1 << 31) - 1),
                      "pair_length_sq": (1, 2), "separated_margin_q15": (-(1 << 63), (1 << 63) - 1)}
            for name in ("valid", "reason", *limits):
                loc = f"/stage_details/{j}/detail/pair_rows/{k}/{name}"
                if name not in row:
                    self.note("missing", "MISSING_SAVED_FIELD", sid, v["id"], {"field": name}, loc)
                    continue
                value = row[name]
                if name == "valid" and type(value) is not bool or name == "reason" and type(value) is not str:
                    raise Issue(3, "SAVED_LAG_FIELD_TYPE", {"field": name})
                if name in limits and (type(value) is not int or not limits[name][0] <= value <= limits[name][1]):
                    raise Issue(3, "SAVED_LAG_FIELD_INTEGER_RANGE", {"field": name})
                out["facts"].append({"name": name, "value": known(json_value(value)), "source_id": sid,
                                     "locator": loc, "degree": "KNOWN_SAVED"})
            if "pair_length_sq" in row and row["pair_length_sq"] != PAIRS[k][4]:
                self.note("conflicts", "SOURCE_PAIR_LENGTH", sid, v["id"], {"source": row["pair_length_sq"], "expected": PAIRS[k][4]})
            units = stage.get("units")
            if type(units) is not dict:
                self.note("missing", "MISSING_SAVED_UNITS", sid, v["id"])
                units = {}
            out["saved_status"] = json_value(units)
            for unit, status in units.items():
                if type(status) is not str:
                    raise Issue(3, "SAVED_UNIT_STATUS_TYPE")
                if status.startswith("ALGORITHM_REJECTED:"):
                    self.original_errors.append(raw_error(sid, f"/stage_details/{j}/units/{unit}", status, "QUALIFICATION", status))
            for name in ("numeric_invalid", "invalid_reasons", "fft_flags", "fixed4", "fixed4_totals", "ifft_flags"):
                if name not in detail:
                    self.note("missing", "MISSING_NUMERIC_AUDIT_FIELD", sid, v["id"], {"field": name})
                else:
                    out["numeric_audit"][name] = {"source_id": sid, "locator": f"/stage_details/{j}/detail/{name}", "original_source_preserved": True}
            if "numeric_invalid" in detail and type(detail["numeric_invalid"]) is not bool:
                raise Issue(3, "SAVED_NUMERIC_INVALID_TYPE")
            if detail.get("numeric_invalid") is True:
                self.note("conflicts", "ORIGINAL_NUMERIC_ERROR_REMAINS_INVALID", sid, v["id"])
            reasons = detail.get("invalid_reasons", [])
            if type(reasons) is not list or any(type(r) is not str for r in reasons):
                raise Issue(3, "ORIGINAL_REASON_LIST_TYPE")
            for n, reason in enumerate(reasons):
                self.original_errors.append(raw_error(sid, f"/stage_details/{j}/detail/invalid_reasons/{n}", reason, "UNKNOWN"))
            # Compare all independently saved duplicates, never synthesize absent members.
            f4 = detail.get("fixed4", {})
            if type(f4) is dict:
                for domain, audit in f4.items():
                    if type(audit) is dict and "frame_identity" in audit:
                        dup = audit["frame_identity"]
                        if type(dup) is not dict:
                            raise Issue(3, "FIXED4_IDENTITY_TYPE")
                        for name in identity.keys() & dup.keys():
                            if dup[name] != identity[name]:
                                self.note("conflicts", "SAVED_DUPLICATE_IDENTITY", sid, v["id"], {"domain": domain, "field": name, "source": identity[name], "duplicate": dup[name]})
            frames = data.get("frames")
            if type(frames) is list and j < len(frames) and type(frames[j]) is dict:
                for a, b in (("frame", "frame"), ("last_id", "last_id")):
                    if a in identity and b in frames[j] and identity[a] != frames[j][b]:
                        self.note("conflicts", "SAVED_FRAME_ROW_IDENTITY", sid, v["id"], {"field": a, "detail": identity[a], "frame_row": frames[j][b]})
            out["processed"] = True
        except Issue as e:
            self.note("conflicts", e.reason, sid, v["id"], e.details)

    def check_links(self, sid, role, data):
        if role == "RESEARCH_CONFIG_FIELDS":
            if data.get("scope") != "RESEARCH_ONLY" or data.get("backend") != "portable_q30_frozen":
                self.note("unsupported", "UNSUPPORTED_RESEARCH_BACKEND_OR_SCOPE", sid)
            facts = []
            for name in ("scope", "profile_id", "backend", "source_manifest_sha256", "table_manifest_sha256", "sample_rate_hz", "frame_length", "hop", "geometry", "activity", "tracker", "audio_fade_samples"):
                if name not in data:
                    self.note("missing", "MISSING_RESEARCH_CONFIG_FIELD", sid, details={"field": name})
                elif name in ("sample_rate_hz", "frame_length", "hop", "audio_fade_samples") and (type(data[name]) is not int or not 0 <= data[name] < (1 << 64)):
                    self.note("conflicts", "RESEARCH_CONFIG_INTEGER_TYPE", sid, details={"field": name})
                else:
                    value = {"source_id": sid, "locator": "/" + name, "original_source_preserved": True} if type(data[name]) in (dict, list) else json_value(data[name])
                    facts.append({"name": name, "value": value, "locator": "/" + name, "degree": "KNOWN_SAVED_RESEARCH_NOT_PRODUCTION"})
            self.support_views.append({"source_id": sid, "role": role, "facts": facts})
            self.histories.append({"source_id": sid, "locator": "/", "original_source_preserved": True,
                                   "native_interpretation": "NOT_RUN", "root_equivalence": "NOT_PROVEN"})
            return
        outputs = data.get("outputs_sha256")
        if type(outputs) is not dict:
            self.note("missing", "MISSING_RUN_INDEX_OUTPUTS", sid)
        else:
            for target, name in (("SAVED_RESULT_FIELDS", "result.json"), ("SAVED_CONTAINER_BYTES", "stages-and-audio.npz")):
                matches = [e for e in self.store.entries.values() if e["id"] in self.required and e["ref"]["schema_id"] in ROLES and ROLES[e["ref"]["schema_id"]][0] == target]
                for e in matches:
                    if name not in outputs:
                        self.note("missing", "MISSING_RUN_INDEX_OUTPUT_HASH", sid, details={"name": name})
                    elif outputs[name] != e["ref"]["content_sha256"]:
                        self.note("conflicts", "RUN_INDEX_OUTPUT_HASH", sid, details={"index": outputs[name], "target": e["ref"]})
                    self.store.edges.append({"from": sid, "to": e["id"], "rule": "RUN_INDEX_OUTPUT_HASH", "locator": "/outputs_sha256/" + name})
        inputs, composer = data.get("inputs_sha256", {}), data.get("composer_sha256", {})
        self.support_views.append({"source_id": sid, "role": role,
                                   "saved_bindings": [{"name": name, "source_id": sid, "locator": "/" + name, "original_source_preserved": True} for name in ("inputs_sha256", "source_identity", "composer_sha256", "outputs_sha256") if name in data]})
        for e in self.store.entries.values():
            if e["id"] not in self.required:
                continue
            schema, code = e["ref"]["schema_id"], e["ref"]["content_sha256"]
            expected = inputs.get("config") if schema == "ss-b-research-config-v1" and type(inputs) is dict else None
            if schema == "ss-b-lag-rule-source-v1" and type(composer) is dict:
                name = RULE_HASHES.get(code)
                expected = composer.get("chain.py") if name == "saved-chain" else composer.get("__main__.py") if name == "saved-writer" else None
            if expected is not None:
                if expected != code:
                    self.note("conflicts", "RUN_INDEX_SOURCE_BINDING", sid, details={"expected": expected, "declared": code, "target_id": e["id"]})
                self.store.edges.append({"from": sid, "to": e["id"], "rule": "RUN_INDEX_SOURCE_BINDING", "locator": "/inputs_sha256 or /composer_sha256"})

    def array_view(self, v):
        if v["array_view"]["state"] == "UNKNOWN":
            self.note("missing", "MISSING_NPZ_MEMBER_VIEW", view=v["id"])
            return
        a = v["array_view"]["value"]
        expected = f"frame{uint(v['stage_ordinal']):04d}_ifft_real.npy"
        if a["member_name"] != expected:
            self.note("conflicts", "WRITER_MEMBER_FRAME_NAME", a["member_id"], v["id"], {"expected": expected, "selected": a["member_name"]})
        parent = self.source(a["container_id"], v["id"])
        member = self.source(a["member_id"], v["id"])
        if parent is None or member is None:
            return
        if self.roles.get(a["container_id"]) != "SAVED_CONTAINER_BYTES" or self.roles.get(a["member_id"]) != "SAVED_MEMBER_LAYOUT":
            self.note("unsupported", "ARRAY_ROLE_MISMATCH", a["member_id"], v["id"])
            return
        try:
            zip_directory(parent)
            layout = npy_layout(member)
            k = uint(a["row_ordinal"], 5)
            start = uint(layout["data_offset"]) + 8192 * k
            out = next(x for x in self.views if x["id"] == v["id"])
            out["array_view"] = {"container_id": a["container_id"], "member_id": a["member_id"], "layout": layout,
                                 "row_byte_span": [str(start), str(start + 8192)], "degree": "DERIVED_LAYOUT_NOT_NUMERIC_DECODE"}
            self.store.edges.append({"from": v["result_id"], "to": a["member_id"], "rule": "SAVED_WRITER_FRAME_PAIR_VIEW", "locator": expected + "#row=" + str(k)})
        except Issue as e:
            self.note("conflicts", e.reason, a["member_id"], v["id"], e.details)

    def report(self):
        result = "FAILED" if self.conflicts else "UNSUPPORTED" if self.unsupported else "INCOMPLETE" if self.missing else "SAVED_FIELDS_EXPORTED"
        processed = sum(v["processed"] for v in self.views)
        return {"schema_id": "ss-b-producer-report-v1", "schema_version": "1", "claim_scope": PROFILE,
                "output_state": "SEALED_REPORT", "producer_result": result, "v_status": "NOT_RUN",
                "counts": {"requested_views": str(len(self.selection["views"])), "processed_views": str(processed),
                           "not_processed_views": str(len(self.selection["views"]) - processed),
                           "permission_sources": str(len(self.store.entries)), "actual_read_sources": str(len(self.store.records)),
                           "conflicts": str(len(self.conflicts)), "missing": str(len(self.missing)),
                           "unsupported": str(len(self.unsupported)), "original_errors": str(len(self.original_errors))},
                "views": self.views, "source_audit": {"permission_set": list(self.store.entries),
                                                     "actual_read_set": self.store.records,
                                                     "consumed_closure": self.consumed, "edges": self.store.edges,
                                                     "closure_status": "INCOMPLETE_CONTEXT_NATIVE_NOT_SUPPLIED",
                                                     **self.store.accounting()},
                "conflicts": self.conflicts, "missing": self.missing, "unsupported": self.unsupported,
                "original_errors": self.original_errors, "error_capacity_issues": error_capacity(self.original_errors),
                "saved_history_refs": self.histories, "raw_payloads": [], "wire_ready": "0", "time": "UNBOUND",
                "support_views": self.support_views,
                "not_run": ["mathematical V", "full K/roots association", "native/lease bridge", "algorithms", "RTL/EDA/hardware"]}
