"""Exclusive-output CLI for the offline evidence consumer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import traceback

from .bundle import BundleError, IdentityError, load_bundle, sha256, validate_structure
from .bundle import verify_references, verify_unchanged
from .report import evaluate

HERE = Path(__file__).resolve().parent
CODE_FILES = ("__init__.py", "__main__.py", "bundle.py", "grid.py", "events.py",
              "metrics.py", "report.py", "README.md")


def _code_hashes() -> dict[str, str]:
    return {name: sha256(HERE / name) for name in CODE_FILES}


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(
        "Offline H3 evidence evaluator. Exit 0 means a report was produced, not PASS. "
        "SYNTHETIC_TEST never yields formal performance PASS."))
    parser.add_argument("--bundle", required=True, type=Path, help="EVIDENCE_BUNDLE_V1 JSON; references stay under its parent")
    parser.add_argument("--out", required=True, type=Path, help="New exclusive output directory")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("OUTPUT_EXISTS")
    # Reserve only our new output. No existing file or directory is removed.
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("OUTPUT_EXISTS")
    except OSError as exc:
        parser.error(f"OUTPUT_UNAVAILABLE:{exc}")
    code_before = {}
    bundle_sha_before = None
    verified = []
    try:
        code_before = _code_hashes()
        bundle, original = load_bundle(args.bundle)
        bundle_sha_before = hashlib.sha256(original).hexdigest()
        verified = verify_references(bundle, args.bundle.parent)
        validate_structure(bundle, verified)
        report = evaluate(bundle, verified)
        report_tmp = args.out / "report.json.pending"
        _write_json(report_tmp, report)
        readme_tmp = args.out / "README.md.pending"
        readme_tmp.write_text(
            "Offline evidence consumer. Exit 0 means report generated; inspect report.status and each axis.\n"
            "SYNTHETIC_TEST and missing real service facts are not formal acceptance.\n", encoding="utf-8")
        verify_unchanged(args.bundle, bundle_sha_before, verified)
        code_after = _code_hashes()
        if code_after != code_before:
            raise IdentityError(f"EVALUATOR_CODE_CHANGED_DURING_RUN:{code_before}:{code_after}")
        index = {"schema_version": "H3_EVALUATOR_RUN_INDEX_V1", "argv": sys.argv if argv is None else argv,
                 "cwd": os.getcwd(), "python": platform.python_version(),
                 "claim_scope": bundle["claim_scope"], "report_status": report["status"],
                 "bundle": {"path": str(args.bundle.resolve()), "sha256": bundle_sha_before,
                            "bytes": len(original)}, "references": verified,
                 "source_sha256": code_before,
                 "outputs_sha256": {"report.json": sha256(report_tmp),
                                    "README.md": sha256(readme_tmp)},
                 "claim_stage": "DIAGNOSTIC_SMOKE_NOT_ACCEPTANCE"}
        index_tmp = args.out / "evidence-index.json.pending"
        _write_json(index_tmp, index)
        verify_unchanged(args.bundle, bundle_sha_before, verified)
        if _code_hashes() != code_before:
            raise IdentityError("EVALUATOR_CODE_CHANGED_BEFORE_PUBLICATION")
        report_tmp.replace(args.out / "report.json")
        readme_tmp.replace(args.out / "README.md")
        index_tmp.replace(args.out / "evidence-index.json")
        return 0
    except (BundleError, IdentityError, OSError) as exc:
        code = 3 if isinstance(exc, IdentityError) else 2
        _write_json(args.out / "failure.json", {"exit_code": code, "error_type": type(exc).__name__,
                   "message": str(exc), "bundle_sha256_before": bundle_sha_before,
                   "verified_references_before": verified, "source_sha256_before": code_before})
        return code
    except BaseException as exc:
        _write_json(args.out / "failure.json", {"exit_code": 4, "error_type": type(exc).__name__,
                   "message": str(exc), "traceback": traceback.format_exc(),
                   "bundle_sha256_before": bundle_sha_before, "verified_references_before": verified,
                   "source_sha256_before": code_before})
        return 4


if __name__ == "__main__":
    sys.exit(main())
