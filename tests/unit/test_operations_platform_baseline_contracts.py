from pathlib import Path

from packages.drone_schemas import OperationsPlatformBaseline, OperationsPlatformModule, load_model


def test_operations_platform_baseline_contract_collects_local_modules() -> None:
    module = OperationsPlatformModule(
        module_id="platform-readiness-index",
        title="Offline platform readiness index",
        source_version="1.9.0",
        artifact_refs=["data/sample_platform/platform_readiness_index.json"],
        validation_commands=[
            "python -m apps.cli.main validate-platform-index --index data/sample_platform/platform_readiness_index.json --out <tmp>/platform_index_validation.json"
        ],
        expected_outputs=["platform_index_validation.json"],
        reviewer_roles=["platform_owner"],
        safety_notes=["offline-only", "advisory-only", "human-review-required"],
    )
    baseline = OperationsPlatformBaseline(
        baseline_id="ops-platform-baseline",
        version="2.0.0",
        title="Offline operations platform baseline",
        modules=[module],
        release_checks=["pytest"],
        safety_boundary={"offline_only": True, "advisory_only": True, "no_real_drone_connection": True},
    )

    assert baseline.module_count == 1
    assert baseline.human_review_required is True
    assert baseline.modules[0].human_review_required is True
    assert baseline.release_checks == ["pytest"]


def test_sample_operations_platform_baseline_loads_with_stable_order() -> None:
    baseline = load_model(Path("data/sample_platform/operations_platform_baseline.json"), OperationsPlatformBaseline)

    assert baseline.baseline_id == "ops-platform-baseline"
    assert baseline.version == "2.0.0"
    assert baseline.module_count >= 8
    assert [module.module_id for module in baseline.modules] == sorted(module.module_id for module in baseline.modules)
    assert "pytest" in baseline.release_checks
    assert baseline.safety_boundary["offline_only"] is True
    assert baseline.safety_boundary["advisory_only"] is True
    assert baseline.safety_boundary["no_real_drone_connection"] is True
