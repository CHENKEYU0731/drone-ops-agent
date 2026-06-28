from pathlib import Path

from packages.drone_schemas import PlatformReadinessCapability, PlatformReadinessIndex, load_model


def test_platform_readiness_index_contract_lists_local_capabilities() -> None:
    capability = PlatformReadinessCapability(
        capability_id="organization-handoff",
        title="Organization handoff package",
        version="1.8.0",
        commands=["python -m apps.cli.main validate-handoff-package --package <package> --out <out>"],
        output_refs=["handoff_validation.json"],
        safety_notes=["offline-only", "advisory-only"],
    )
    index = PlatformReadinessIndex(
        index_id="platform-readiness-index",
        version="1.9.0",
        capabilities=[capability],
        required_release_checks=["pytest"],
        safety_boundary={"offline_only": True, "advisory_only": True},
    )

    assert index.capability_count == 1
    assert index.human_review_required is True
    assert index.capabilities[0].human_review_required is True
    assert index.required_release_checks == ["pytest"]


def test_sample_platform_readiness_index_loads_with_stable_order() -> None:
    index = load_model(Path("data/sample_platform/platform_readiness_index.json"), PlatformReadinessIndex)

    assert index.index_id == "platform-readiness-index"
    assert index.version == "1.9.0"
    assert index.capability_count >= 8
    assert [capability.capability_id for capability in index.capabilities] == sorted(
        capability.capability_id for capability in index.capabilities
    )
    assert "pytest" in index.required_release_checks
    assert index.safety_boundary["offline_only"] is True
    assert index.safety_boundary["advisory_only"] is True
