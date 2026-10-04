"""RAW R1 research diagnostics, always audit.NOT_RUN, never CHECKED_SOURCE."""
import json

from .contracts import PROFILE, RAW, SPEC, PAIRS, MIB, unknown, known


def serialize(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def payload(view, producer):
    if not view["processed"]:
        return None, "Selected saved fields not processed"
    k = int(view["selection"]["pair_ordinal"])
    pair = PAIRS[k]
    ids = [sid for sid in producer.consumed if sid in producer.store.by_id]
    if len(ids) > 256:
        return None, "RAW Object capacity exceeded; complete original sources retained"
    object_ids = {sid: f"source-{i}" for i, sid in enumerate(ids)}
    objects = []
    for sid in ids:
        e = producer.store.entries[sid]
        rule = producer.roles.get(sid) == "WHITELIST_RULE_BYTES"
        objects.append({"id": object_ids[sid], "ref": e["ref"], "byte_length": e["byte_length"],
                        "producer": "New offline wrapper of fixed saved bytes; not original native producer",
                        "provenance": "RULE_SOURCE" if rule else "SAVED_RESEARCH_INSTANCE",
                        "key_wire": unknown("Full independently sourced K not supplied"),
                        "pair_index": unknown("Global rule applicability only") if rule else known(str(k)),
                        "lifetime": unknown("Original native lifetime/lease not supplied")})
    facts = []
    source_id = view["selection"]["result_id"]
    aliases = {"delta_q12": "delta", "tau_q12": "tau", "physical_limit_q12": "T",
               "pair_length_sq": "L", "valid": "qualified", "reason": "research_reason"}
    for f in view["facts"]:
        val = f["value"]["value"]
        if type(val) is bool:
            value = known({"type": "BOOL", "data": val})
        elif f["name"] == "reason":
            value = known({"type": "UTF8", "data": val}) if len(val.encode("utf-8")) <= 1024 else unknown("Original reason exceeds RAW Text; retained in source Object")
        else:
            if len(val.lstrip("-")) > 256:
                return None, "RAW Int representation exceeded"
            value = known({"type": "INT", "data": val})
        facts.append({"id": f"fact-{len(facts)}", "name": aliases.get(f["name"], f["name"]), "value": value,
                      "provenance": "SAVED_RESEARCH_INSTANCE", "source_ids": [object_ids[source_id]], "locator": f["locator"]})
    result = {"schema_id": "ss-lag-proof-raw-v1", "schema_version": "1", "profile": PROFILE,
              "key_wire": unknown("Full K not acquired; partial original values are in report"),
              "roots_wire": unknown("Independent ordered config/numeric/geometry root originals not supplied"),
              "pair": {"index": str(k), "channels": [str(pair[0]), str(pair[1])], "unit_index": str(pair[3]), "unit_name": pair[2]},
              "objects": objects, "facts": facts, "events": [],
              "audit": {"verifier": unknown("Mathematical V NOT_RUN"),
                        "specification": {"schema_id": "ss-b-lag-decoder-v-spec", "schema_version": "1",
                                          "schema_sha256": SPEC, "encoding": "RAW_BYTES", "content_sha256": SPEC},
                        "input_ids": list(object_ids.values()), "derived_facts": [], "result": "NOT_RUN",
                        "log": unknown("No V execution or verifier log")},
              "coverage": [{"requirement": f"P{i:02d}", "state": "NOT_OBTAINED", "evidence_ids": [],
                            "missing": "No obligation verifier executed; saved fields separately retained"} for i in range(1, 31)],
              "limitations": ["Partial saved-research export only; source conflicts/missing/unsupported are in report",
                              "No full K/roots, native execution/lifetime, mathematical V, production or receiver projection"]}
    b = serialize(result)
    if len(b) > MIB:
        return None, "RAW byte limit exceeded; complete original sources retained"
    return b, None
