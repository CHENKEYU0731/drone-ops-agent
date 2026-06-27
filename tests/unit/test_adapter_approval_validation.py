from pathlib import Path

from packages.adapter_workflows import validate_adapter_registry, validate_approval_packet


def test_validate_adapter_registry_passes_sample_registry() -> None:
    result = validate_adapter_registry(Path("data/sample_adapters/offline_adapter_registry.json"))

    assert result["status"] == "PASS"
    assert result["counts"]["adapters"] == 3
    assert result["counts"]["findings"] == 0
    assert result["safety_boundary"]["offline_only"] is True
    assert result["human_review_required"] is True


def test_validate_approval_packet_passes_sample_packet() -> None:
    result = validate_approval_packet(Path("data/sample_approvals/approval_packet.json"))

    assert result["status"] == "PASS"
    assert result["counts"]["approvals"] == 2
    assert result["counts"]["findings"] == 0
    assert result["human_review_required"] is True


def test_validate_approval_packet_requires_rationale(tmp_path: Path) -> None:
    packet_path = tmp_path / "approval_packet.json"
    packet_path.write_text(
        """
{
  "packet_id": "approval-packet-broken",
  "subject_ref": "bundle-uav-001-demo",
  "approvals": [
    {
      "approval_id": "approval-missing-rationale",
      "subject_ref": "bundle-uav-001-demo",
      "reviewer_id": "reviewer-local",
      "reviewer_role": "maintenance_lead",
      "decision": "APPROVED",
      "rationale": "",
      "evidence_refs": [],
      "generated_by_skill": "platform-readiness",
      "skill_version": "1.5.0"
    }
  ],
  "required_roles": ["maintenance_lead"],
  "safety_boundary": {"offline_only": true, "advisory_only": true},
  "generated_by_skill": "approval-workflow",
  "skill_version": "1.7.0"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = validate_approval_packet(packet_path)

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["findings"][0]["code"] == "APPROVAL_RATIONALE_MISSING"
