from pathlib import Path

from packages.operations_platform import validate_operations_platform


def test_validate_operations_platform_passes_sample_baseline() -> None:
    result = validate_operations_platform(Path("data/sample_platform/operations_platform_baseline.json"))

    assert result["status"] == "PASS"
    assert result["counts"]["modules"] >= 8
    assert result["counts"]["findings"] == 0
    assert result["safety_boundary"]["offline_only"] is True
    assert result["safety_boundary"]["advisory_only"] is True
    assert result["safety_boundary"]["no_real_maintenance_system"] is True
    assert result["human_review_required"] is True


def test_validate_operations_platform_reports_missing_validation_command(tmp_path: Path) -> None:
    baseline_path = tmp_path / "operations_platform_baseline.json"
    baseline_path.write_text(
        """
{
  "id": "OPSBASE-broken",
  "timestamp": "1970-01-01T00:00:00Z",
  "drone_id": null,
  "human_review_required": true,
  "generated_by_skill": "operations-platform-baseline",
  "skill_version": "2.0.0",
  "baseline_id": "ops-platform-broken",
  "version": "2.0.0",
  "title": "Broken offline operations platform baseline",
  "modules": [
    {
      "id": "OPSMOD-broken",
      "timestamp": "1970-01-01T00:00:00Z",
      "drone_id": null,
      "human_review_required": true,
      "generated_by_skill": "operations-platform-baseline",
      "skill_version": "2.0.0",
      "module_id": "broken-module",
      "title": "Broken module",
      "source_version": "2.0.0",
      "artifact_refs": ["missing.json"],
      "validation_commands": [],
      "expected_outputs": ["broken_validation.json"],
      "reviewer_roles": ["platform_owner"],
      "safety_notes": ["offline-only"]
    }
  ],
  "release_checks": ["pytest"],
  "safety_boundary": {
    "offline_only": true,
    "advisory_only": true,
    "human_review_required": true,
    "no_real_drone_connection": true,
    "no_mavlink_command_execution": true,
    "no_external_platform_connection": true,
    "no_real_maintenance_system": true,
    "no_auto_dispatch": true,
    "no_simulator_launch": true
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = validate_operations_platform(baseline_path)

    assert result["status"] == "REVIEW_REQUIRED"
    assert "OPS_PLATFORM_MODULE_VALIDATION_COMMANDS_MISSING" in {finding["code"] for finding in result["findings"]}
