from __future__ import annotations

from pathlib import Path
from typing import Any


DETERMINISTIC_GENERATED_AT = "1970-01-01T00:00:00Z"


def build_dashboard_bundle(
    *,
    report_dir: Path,
    fleet_summary: Path | None = None,
    fleet_report: Path | None = None,
    reference_root: Path | None = None,
) -> dict[str, Any]:
    report_dir = Path(report_dir)
    reference_root = Path(reference_root) if reference_root is not None else None
    return {
        "schema_version": 1,
        "bundle_id": "DASHBOARD-BUNDLE-OFFLINE",
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "human_review_required": True,
        "safety_boundary": {
            "offline_only": True,
            "read_only": True,
            "advisory_only": True,
            "real_drone_connection": False,
            "external_platform_connection": False,
        },
        "sections": [
            "report",
            "simulation",
            "work_orders",
            "fleet_health",
            "audit",
            "evidence",
        ],
        "artifacts": {
            "report": {
                "report_dir": _ref(report_dir, reference_root),
                "ops_report_md": _optional_ref(report_dir / "ops_report.md", reference_root),
                "report_validation": _optional_ref(report_dir / "report_validation.json", reference_root),
            },
            "simulation": {
                "simulation_run": _optional_ref(report_dir / "simulation_run.json", reference_root),
            },
            "work_orders": {
                "work_order_drafts": _optional_ref(report_dir / "work_order_drafts.json", reference_root),
                "work_order_validation": _optional_ref(report_dir / "work_order_validation.json", reference_root),
            },
            "fleet_health": {
                "fleet_health_summary": _optional_ref(fleet_summary, reference_root),
                "fleet_health_report": _optional_ref(fleet_report, reference_root),
            },
            "audit": {
                "audit_dir": _optional_ref(report_dir / "audit", reference_root),
            },
            "evidence": {
                "evidence_index": _optional_ref(report_dir / "evidence_index.json", reference_root),
            },
        },
    }


def _ref(path: Path, reference_root: Path | None = None) -> str:
    if reference_root is not None:
        path = path.relative_to(reference_root)
    return path.as_posix()


def _optional_ref(path: Path | None, reference_root: Path | None = None) -> str | None:
    if path is None:
        return None
    return _ref(path, reference_root)
