from pathlib import Path

from packages.platform_index import validate_platform_index


def test_validate_platform_index_passes_sample_index() -> None:
    result = validate_platform_index(Path("data/sample_platform/platform_readiness_index.json"))

    assert result["status"] == "PASS"
    assert result["counts"]["capabilities"] >= 8
    assert result["counts"]["findings"] == 0
    assert result["safety_boundary"]["offline_only"] is True
    assert result["safety_boundary"]["advisory_only"] is True
    assert result["human_review_required"] is True


def test_validate_platform_index_reports_missing_command(tmp_path: Path) -> None:
    index_path = tmp_path / "platform_readiness_index.json"
    index_path.write_text(
        """
{
  "id": "PLATFORMINDEX-broken",
  "timestamp": "1970-01-01T00:00:00Z",
  "drone_id": null,
  "human_review_required": true,
  "generated_by_skill": "platform-readiness-index",
  "skill_version": "1.9.0",
  "index_id": "platform-readiness-index-broken",
  "version": "1.9.0",
  "capabilities": [
    {
      "id": "PLATFORMCAP-broken",
      "timestamp": "1970-01-01T00:00:00Z",
      "drone_id": null,
      "human_review_required": true,
      "generated_by_skill": "platform-readiness-index",
      "skill_version": "1.9.0",
      "capability_id": "broken-capability",
      "title": "Broken capability",
      "version": "1.9.0",
      "commands": [],
      "output_refs": ["broken.json"],
      "safety_notes": ["offline-only"]
    }
  ],
  "required_release_checks": ["pytest"],
  "safety_boundary": {
    "offline_only": true,
    "advisory_only": true,
    "human_review_required": true,
    "no_real_drone_connection": true,
    "no_mavlink_command_execution": true,
    "no_external_platform_connection": true,
    "no_auto_dispatch": true
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = validate_platform_index(index_path)

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["findings"][0]["code"] == "PLATFORM_CAPABILITY_COMMANDS_MISSING"
