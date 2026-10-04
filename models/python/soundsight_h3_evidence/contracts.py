"""Pinned research interfaces and bounded JSON admission, not a RAW verifier."""
import hashlib
import json
import re

MIB = 1 << 20
SPEC = "6931206cc7dc89f992913e8231a5c95604bcafb5e1a7faec1facf4a08329f5ed"
RAW = "902fb37e4b7533c22c8b59d1c3b011f7820df3e5063ccff994b940496464cbc2"
PROFILE = "SAVED_RESEARCH_DIAGNOSTIC"
RULE_HASHES = {
    "30a9a550d4303d464dc2e56d8b2ce38774b49c1d8e313bc70efbc0c4b06c5924": "B-r2",
    "f6bb2bc41dee3f1e2e6d93176972d92db12d687978fd3a95a47e85b28f88a74a": "lag-leaf",
    "57ca9e425fafd4da73c83edea152f185664a0c323d71f00de3fe22d4ce14d694": "saved-chain",
    "7a0846bfdd5ac03105806544a4dd0533410616737df347ad199282198e325714": "git-chain-reference",
    "60fad93ed58686ed559a677fa7481dc66be4af662f7cb109fa4e0ae90f75adb2": "saved-writer",
    "cf8ddee41d668c7541f4f5c218705f962fb9a204e5af39524adb6f0e36c42305": "git-writer-reference",
    "257a5b358d344f59b41766a6893854b554dc478a8196acc3aab3f819ddf3d3dd": "parent-wire",
}
ROLES = {
    "ss-b-saved-portable-result-v1": ("SAVED_RESULT_FIELDS", "SELECTED_FRAME_PAIR"),
    "ss-b-saved-run-index-v1": ("SAVED_RUN_LINKS", "RUN_ASSOCIATION"),
    "ss-b-research-config-v1": ("RESEARCH_CONFIG_FIELDS", "RESEARCH_APPLICABILITY"),
    "ss-b-saved-ifft-npz-v1": ("SAVED_CONTAINER_BYTES", "CONTAINER_VIEW"),
    "ss-b-saved-ifft-npy-v1": ("SAVED_MEMBER_LAYOUT", "SELECTED_FRAME_PAIR"),
    "ss-b-lag-rule-source-v1": ("WHITELIST_RULE_BYTES", "WHITELIST_GLOBAL_RULE"),
}
PAIRS = ((0, 1, "lag_01", 34, 1), (0, 2, "lag_02", 37, 2),
         (0, 3, "lag_03", 40, 1), (1, 2, "lag_12", 43, 1),
         (1, 3, "lag_13", 46, 2), (2, 3, "lag_23", 49, 1))


class Issue(Exception):
    def __init__(self, code, reason, details=None):
        super().__init__(reason)
        self.code, self.reason, self.details = code, reason, details or {}


class Resource(Issue):
    def __init__(self, reason, details=None):
        super().__init__(0, reason, details)


def digest(b):
    return hashlib.sha256(b).hexdigest()


def binding(b):
    return {"sha256": digest(b), "byte_length": str(len(b))}


def unknown(reason):
    return {"state": "UNKNOWN", "reason": reason}


def known(value):
    return {"state": "KNOWN", "value": value}


def fields(x, names):
    if type(x) is not dict or set(x) != set(names.split()):
        raise Issue(2, "CONTROL_FIELD_SET", {"required": names})


def text(x, low=0, high=1024):
    if type(x) is not str:
        raise Issue(2, "CONTROL_STRING_REQUIRED")
    try:
        n = len(x.encode("utf-8"))
    except UnicodeError as e:
        raise Issue(2, "INVALID_UNICODE") from e
    if not low <= n <= high:
        raise Issue(2, "CONTROL_STRING_LENGTH")
    return x


def ident(x):
    return text(x, 1, 64)


def uint(x, maximum=(1 << 64) - 1):
    if type(x) is not str or not re.fullmatch(r"0|[1-9][0-9]{0,19}", x) or int(x) > maximum:
        raise Issue(2, "CONTROL_DECIMAL_RANGE")
    return int(x)


def hashcode(x):
    if type(x) is not str or not re.fullmatch(r"[0-9a-f]{64}", x) or x == "0" * 64:
        raise Issue(2, "CONTROL_HASH")
    return x


def filebinding(x):
    fields(x, "sha256 byte_length")
    hashcode(x["sha256"])
    uint(x["byte_length"])


def ref(x):
    fields(x, "schema_id schema_version schema_sha256 encoding content_sha256")
    ident(x["schema_id"])
    ident(x["schema_version"])
    hashcode(x["schema_sha256"])
    hashcode(x["content_sha256"])
    if x["encoding"] not in ("RAW_BYTES", "SS_CANONICAL_JSON_V1"):
        raise Issue(2, "CONTROL_ENCODING")


def maybe(x, validator):
    if type(x) is not dict:
        raise Issue(2, "CONTROL_MAYBE")
    if x.get("state") == "UNKNOWN":
        fields(x, "state reason")
        text(x["reason"], 1)
    elif x.get("state") == "KNOWN":
        fields(x, "state value")
        validator(x["value"])
    else:
        raise Issue(2, "CONTROL_MAYBE_STATE")


def array(x, maximum, minimum=0):
    if type(x) is not list or not minimum <= len(x) <= maximum:
        raise Issue(2, "CONTROL_ARRAY_LIMIT")
    return x


def unique_ids(xs):
    if len(xs) != len(set(xs)):
        raise Issue(2, "CONTROL_DUPLICATE_ID")


def _pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("DUPLICATE_DECODED_KEY")
        result[k] = v
    return result


def _integer(s):
    if not re.fullmatch(r"0|-?[1-9][0-9]{0,255}", s):
        raise ValueError("LEGACY_INTEGER_LEXICAL_OR_DIGIT_LIMIT")
    return int(s)


def _reject(s):
    raise ValueError("UNSUPPORTED_NUMBER_TOKEN:" + s[:32])


def bounded_json(b, control=False):
    """Lexical size/depth/node preflight BEFORE materializing a JSON object tree.

    One string is decoded at a time during preflight. Per-string raw escapes are
    bounded by the admitted source bytes; no unbounded streaming allocations.
    Structural grammar and decoded duplicate keys are then checked by json.loads.
    """
    code = 2 if control else 3
    if b.startswith(b"\xef\xbb\xbf"):
        raise Issue(code, "JSON_BOM")
    if len(b) > (MIB if control else 16 * MIB):
        if control:
            raise Issue(2, "CONTROL_BYTE_LIMIT")
        raise Resource("LEGACY_BYTE_LIMIT")
    try:
        s = b.decode("utf-8", errors="strict")
        i = depth = nodes = total_strings = 0
        while i < len(s):
            ch = s[i]
            if ch in " \t\r\n":
                i += 1
                continue
            if ch == '"':
                end = i + 1
                escaped = False
                while end < len(s):
                    c = s[end]
                    if c == '"' and not escaped:
                        break
                    if c == "\\" and not escaped:
                        escaped = True
                    else:
                        escaped = False
                    end += 1
                if end == len(s):
                    raise ValueError("UNTERMINATED_STRING")
                token = json.loads(s[i:end + 1])
                size = len(token.encode("utf-8", errors="strict"))
                if size > MIB:
                    raise Resource("JSON_STRING_BYTE_LIMIT")
                total_strings += size
                if total_strings > 16 * MIB:
                    raise Resource("JSON_DECODED_STRING_TOTAL_LIMIT")
                nodes += 1
                i = end + 1
            else:
                if ch in "[{":
                    depth += 1
                    nodes += 1
                    if depth > (16 if control else 64):
                        raise Resource("JSON_DEPTH_LIMIT")
                elif ch in "]}":
                    depth -= 1
                elif ch not in ",:":
                    nodes += 1
                    end = i
                    while end < len(s) and s[end] not in ' \t\r\n,]}:{["':
                        end += 1
                    if end == i:
                        raise ValueError("JSON_TOKEN")
                    i = end
                    continue
                i += 1
            if nodes > 250000:
                raise Resource("JSON_NODE_LIMIT")
        result = json.loads(s, object_pairs_hook=_pairs,
                            parse_int=_reject if control else _integer,
                            parse_float=_reject, parse_constant=_reject)
        return result
    except Resource as e:
        if control:
            raise Issue(2, e.reason) from e
        raise
    except (ValueError, UnicodeError, RecursionError) as e:
        raise Issue(code, "JSON_REJECTED", {"reason": str(e)}) from e


def common(x, name, required):
    fields(x, required)
    if x["schema_id"] != name or x["schema_version"] != "1":
        raise Issue(2, "CONTROL_VERSION_OR_SCHEMA")
    if x["proposal_state"] != "PROPOSED_NOT_ACTIVE" or x["profile"] != PROFILE:
        raise Issue(2, "CONTROL_PROFILE_OR_PROPOSAL_STATE")


def validate_controls(am, selection, registry):
    common(am, "ss-b-producer-access-map-v1", "schema_id schema_version proposal_state profile registry_binding read_budget_bytes entries")
    common(selection, "ss-b-producer-selection-v1", "schema_id schema_version proposal_state profile access_map_binding registry_binding views")
    common(registry, "ss-b-producer-registry-v1", "schema_id schema_version proposal_state profile decoder_specification raw_specification entries")
    for x in (am["registry_binding"], selection["access_map_binding"], selection["registry_binding"], registry["decoder_specification"], registry["raw_specification"]):
        filebinding(x)
    uint(am["read_budget_bytes"])
    entries = array(am["entries"], 256, 1)
    refs, paths = [], []
    for e in entries:
        fields(e, "id ref byte_length location")
        ident(e["id"]); ref(e["ref"]); uint(e["byte_length"])
        refs.append(tuple(sorted(e["ref"].items())))
        loc = e["location"]
        if type(loc) is not dict:
            raise Issue(2, "CONTROL_LOCATION")
        if loc.get("kind") == "FILE":
            fields(loc, "kind path")
            text(loc["path"], 1, 4096)
            paths.append(loc["path"].replace("\\", "/").casefold())
        elif loc.get("kind") == "ZIP_MEMBER":
            fields(loc, "kind container_id member_name")
            ident(loc["container_id"]); ident(loc["member_name"])
            name = loc["member_name"]
            if "\\" in name or "\x00" in name or name.startswith("/") or any(p in ("", ".", "..") for p in name.split("/")) or ":" in name:
                raise Issue(2, "CONTROL_MEMBER_NAME")
        else:
            raise Issue(2, "CONTROL_LOCATION_KIND")
    unique_ids([e["id"] for e in entries]); unique_ids(refs); unique_ids(paths)
    ids = {e["id"]: e for e in entries}
    for e in entries:
        loc = e["location"]
        if loc["kind"] == "ZIP_MEMBER" and (loc["container_id"] not in ids or ids[loc["container_id"]]["location"]["kind"] != "FILE"):
            raise Issue(2, "CONTROL_MEMBER_PARENT")
    registrations = array(registry["entries"], 32, 1)
    schemas = []
    for e in registrations:
        fields(e, "id source_schema decoder_role scope_rule whitelist")
        ident(e["id"])
        fields(e["source_schema"], "schema_id schema_version schema_sha256 encoding")
        ref({**e["source_schema"], "content_sha256": "1" * 64})
        ident(e["decoder_role"]); ident(e["scope_rule"])
        schemas.append(tuple(sorted(e["source_schema"].items())))
        for b in array(e["whitelist"], 256, 1):
            filebinding(b)
        unique_ids([(b["sha256"], b["byte_length"]) for b in e["whitelist"]])
    unique_ids([e["id"] for e in registrations]); unique_ids(schemas)
    views = array(selection["views"], 256, 1)
    tuples = []
    for v in views:
        fields(v, "id result_id stage_ordinal pair_ordinal array_view context_id support_ids")
        ident(v["id"]); ident(v["result_id"]); uint(v["stage_ordinal"]); uint(v["pair_ordinal"], 5)
        if v["result_id"] not in ids:
            raise Issue(2, "CONTROL_RESULT_REFERENCE")
        maybe(v["context_id"], ident)
        if v["context_id"]["state"] == "KNOWN" and v["context_id"]["value"] not in ids:
            raise Issue(2, "CONTROL_CONTEXT_REFERENCE")
        def av(a):
            fields(a, "container_id member_id member_name row_ordinal")
            for k in ("container_id", "member_id", "member_name"):
                ident(a[k])
            uint(a["row_ordinal"], 5)
            if a["container_id"] not in ids or a["member_id"] not in ids or a["row_ordinal"] != v["pair_ordinal"]:
                raise Issue(2, "CONTROL_ARRAY_REFERENCE")
            loc = ids[a["member_id"]]["location"]
            if loc != {"kind": "ZIP_MEMBER", "container_id": a["container_id"], "member_name": a["member_name"]}:
                raise Issue(2, "CONTROL_ARRAY_PARENT_BINDING")
        maybe(v["array_view"], av)
        for sid in array(v["support_ids"], 32):
            ident(sid)
            if sid not in ids:
                raise Issue(2, "CONTROL_SUPPORT_REFERENCE")
        unique_ids(v["support_ids"])
        tuples.append((v["result_id"], v["stage_ordinal"], v["pair_ordinal"], json.dumps(v["array_view"], sort_keys=True), json.dumps(v["context_id"], sort_keys=True)))
    unique_ids([v["id"] for v in views]); unique_ids(tuples)
    return ids
