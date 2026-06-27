from pathlib import Path

from packages.dataset_registry import validate_dataset_registry


def test_validate_dataset_registry_passes_sample_registry() -> None:
    result = validate_dataset_registry(Path("data/sample_datasets/registry.json"))

    assert result["status"] == "PASS"
    assert result["counts"]["cases"] >= 6
    assert result["counts"]["findings"] == 0
    assert result["safety_boundary"]["offline_only"] is True
    assert result["human_review_required"] is True


def test_validate_dataset_registry_reports_missing_source_refs(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    registry.write_text(
        """
{
  "registry_id": "broken-registry",
  "version": "1.6.0",
  "generated_by_skill": "dataset-registry",
  "skill_version": "1.6.0",
  "cases": [
    {
      "case_id": "missing-file",
      "case_type": "flight_log",
      "title": "Missing file",
      "source_refs": ["missing.json"],
      "sanitized_status": "sanitized_sample",
      "capabilities": ["analyze-log"],
      "recommended_commands": ["python -m apps.cli.main analyze-log --log missing.json --asset data/sample_assets/uav_001.json --out <tmp>"],
      "expected_outputs": ["flight_summary.json"],
      "safety_boundary": {"offline_only": true, "advisory_only": true}
    }
  ],
  "source_refs": [],
  "safety_boundary": {"offline_only": true, "advisory_only": true}
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = validate_dataset_registry(registry)

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["findings"][0]["code"] == "SOURCE_REF_MISSING"
