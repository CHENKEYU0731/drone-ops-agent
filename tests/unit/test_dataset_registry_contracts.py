from pathlib import Path

from packages.drone_schemas import DatasetCase, DatasetRegistry, load_model


def test_dataset_registry_contract_describes_local_cases() -> None:
    case = DatasetCase(
        case_id="sample-log-json",
        case_type="flight_log",
        title="Sample JSON flight log",
        source_refs=["data/sample_logs/example_flight.json"],
        sanitized_status="sanitized_sample",
        capabilities=["analyze-log", "run-mvp"],
        recommended_commands=[
            "python -m apps.cli.main analyze-log --format json --log data/sample_logs/example_flight.json --asset data/sample_assets/uav_001.json --out <tmp>"
        ],
        expected_outputs=["flight_summary.json", "anomalies.json"],
        safety_boundary={"offline_only": True, "advisory_only": True},
    )
    registry = DatasetRegistry(
        registry_id="sample-dataset-registry",
        version="1.6.0",
        cases=[case],
        source_refs=["data/sample_datasets/registry.json"],
        safety_boundary={"offline_only": True, "advisory_only": True},
    )

    assert registry.case_count == 1
    assert registry.human_review_required is True
    assert registry.cases[0].human_review_required is True
    assert registry.cases[0].source_refs == ["data/sample_logs/example_flight.json"]


def test_sample_dataset_registry_fixture_loads_with_stable_case_order() -> None:
    registry = load_model(Path("data/sample_datasets/registry.json"), DatasetRegistry)

    assert registry.registry_id == "sample-dataset-registry"
    assert registry.version == "1.6.0"
    assert registry.case_count >= 6
    assert [case.case_id for case in registry.cases] == sorted(case.case_id for case in registry.cases)
    assert registry.safety_boundary["offline_only"] is True
