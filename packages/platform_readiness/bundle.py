from __future__ import annotations

import hashlib
from pathlib import Path

from packages.drone_schemas import ReportBundleManifest


SKILL_NAME = "platform-readiness"
SKILL_VERSION = "1.5.0"
DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00Z"


def build_report_bundle_manifest(
    *,
    report_dir: Path,
    workspace_project_id: str,
    bundle_id: str,
    drone_id: str | None = None,
) -> ReportBundleManifest:
    report_dir = Path(report_dir)
    if not report_dir.exists() or not report_dir.is_dir():
        raise FileNotFoundError(f"report directory missing: {report_dir}")
    file_refs = _collect_file_refs(report_dir)
    manifest_hash = _manifest_hash(report_dir, file_refs)
    return ReportBundleManifest(
        id=f"BUNDLE-{bundle_id}",
        timestamp=DETERMINISTIC_TIMESTAMP,
        drone_id=drone_id,
        bundle_id=bundle_id,
        workspace_project_id=workspace_project_id,
        source_report_dir=str(report_dir),
        file_refs=file_refs,
        manifest_hash=f"sha256:{manifest_hash}",
        export_format="directory-json",
        safety_boundary={
            "offline_only": True,
            "advisory_only": True,
            "human_review_required": True,
            "no_external_upload": True,
            "no_real_platform_connection": True,
        },
        human_review_required=True,
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
    )


def _collect_file_refs(report_dir: Path) -> list[str]:
    files = [path for path in report_dir.rglob("*") if path.is_file()]
    return sorted(path.relative_to(report_dir).as_posix() for path in files)


def _manifest_hash(report_dir: Path, file_refs: list[str]) -> str:
    digest = hashlib.sha256()
    for ref in file_refs:
        digest.update(ref.encode("utf-8"))
        digest.update(b"\0")
        digest.update((report_dir / ref).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
