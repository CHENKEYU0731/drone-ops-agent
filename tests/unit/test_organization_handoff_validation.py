from pathlib import Path

from packages.organization_handoff import validate_handoff_package


def test_validate_handoff_package_passes_sample_package() -> None:
    result = validate_handoff_package(Path("data/sample_handoff/organization_handoff_package.json"))

    assert result["status"] == "PASS"
    assert result["counts"]["artifacts"] >= 6
    assert result["counts"]["findings"] == 0
    assert result["safety_boundary"]["offline_only"] is True
    assert result["safety_boundary"]["advisory_only"] is True
    assert result["human_review_required"] is True


def test_validate_handoff_package_reports_missing_required_artifact(tmp_path: Path) -> None:
    package_path = tmp_path / "organization_handoff_package.json"
    package_path.write_text(
        """
{
  "id": "HANDOFF-broken",
  "timestamp": "1970-01-01T00:00:00Z",
  "drone_id": null,
  "human_review_required": true,
  "generated_by_skill": "organization-handoff",
  "skill_version": "1.8.0",
  "package_id": "org-handoff-broken",
  "version": "1.8.0",
  "title": "Broken handoff package",
  "workspace_project_id": "workspace-local-demo",
  "artifact_refs": [
    {
      "id": "HANDOFFART-missing",
      "timestamp": "1970-01-01T00:00:00Z",
      "drone_id": null,
      "human_review_required": true,
      "generated_by_skill": "organization-handoff",
      "skill_version": "1.8.0",
      "artifact_id": "missing-required-artifact",
      "artifact_type": "workspace_project",
      "path": "missing/workspace_project.json",
      "required": true,
      "description": "Missing required artifact."
    }
  ],
  "reviewer_roles": ["maintenance_lead"],
  "safety_boundary": {
    "offline_only": true,
    "advisory_only": true,
    "human_review_required": true,
    "no_real_drone_connection": true,
    "no_external_platform_connection": true,
    "no_auto_dispatch": true
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = validate_handoff_package(package_path)

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["findings"][0]["code"] == "HANDOFF_ARTIFACT_MISSING"
