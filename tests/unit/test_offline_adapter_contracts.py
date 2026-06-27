from pathlib import Path

from packages.drone_schemas import OfflineAdapterContract, OfflineAdapterRegistry, load_model


def test_offline_adapter_registry_contract_keeps_operations_local() -> None:
    adapter = OfflineAdapterContract(
        adapter_id="mock-work-order-export",
        adapter_type="work_order_export",
        direction="export",
        allowed_operations=["render_local_file"],
        prohibited_operations=["api_call", "auto_dispatch", "mavlink_command"],
        safety_boundary={"offline_only": True, "advisory_only": True},
    )
    registry = OfflineAdapterRegistry(
        registry_id="offline-adapter-registry",
        version="1.7.0",
        adapters=[adapter],
        source_refs=["data/sample_adapters/offline_adapter_registry.json"],
        safety_boundary={"offline_only": True, "advisory_only": True},
    )

    assert registry.adapter_count == 1
    assert registry.human_review_required is True
    assert registry.adapters[0].human_review_required is True
    assert registry.adapters[0].prohibited_operations == ["api_call", "auto_dispatch", "mavlink_command"]


def test_sample_offline_adapter_registry_loads_with_stable_order() -> None:
    registry = load_model(Path("data/sample_adapters/offline_adapter_registry.json"), OfflineAdapterRegistry)

    assert registry.registry_id == "offline-adapter-registry"
    assert registry.version == "1.7.0"
    assert registry.adapter_count == 3
    assert [adapter.adapter_id for adapter in registry.adapters] == sorted(adapter.adapter_id for adapter in registry.adapters)
    assert registry.safety_boundary["offline_only"] is True
