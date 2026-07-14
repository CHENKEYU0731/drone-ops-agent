import hashlib
import json
from pathlib import Path

import pytest

from packages.open_source_logs import (
    load_open_source_log_registry,
    validate_open_source_log_registry,
    verify_cached_source,
)


REGISTRY_PATH = Path("data/open_source_logs/registry.json")


def test_open_source_log_registry_pins_license_commit_size_and_hash() -> None:
    registry = load_open_source_log_registry(REGISTRY_PATH)
    validation = validate_open_source_log_registry(REGISTRY_PATH)

    assert len(registry.sources) == 3
    assert [source.source_id for source in registry.sources] == sorted(source.source_id for source in registry.sources)
    assert all(source.license_spdx == "BSD-3-Clause" for source in registry.sources)
    assert all(len(source.commit) == 40 and source.commit in source.download_url for source in registry.sources)
    assert all(len(source.sha256) == 64 for source in registry.sources)
    assert all(source.real_world_flight_verified is False for source in registry.sources)
    assert validation["status"] == "PASS"
    assert validation["all_real_world_flight_verified"] is False


def test_registry_cannot_self_attest_real_world_flight(tmp_path: Path) -> None:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["sources"][0]["real_world_flight_verified"] = True
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="no real-world flight attestation mechanism"):
        load_open_source_log_registry(path)


def test_verify_cached_source_accepts_exact_size_and_hash(tmp_path: Path) -> None:
    source_file = Path("data/sample_logs/example_px4_mock.ulg")
    payload = source_file.read_bytes()
    commit = "a" * 40
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "registry_id": "TEST",
                "description": "test",
                "sources": [
                    {
                        "source_id": "test-source",
                        "title": "test",
                        "repository": "example/test",
                        "commit": commit,
                        "source_path": "test/example_px4_mock.ulg",
                        "download_url": f"https://raw.githubusercontent.com/example/test/{commit}/test/example_px4_mock.ulg",
                        "filename": "example_px4_mock.ulg",
                        "format": "px4-ulog",
                        "size_bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "license_spdx": "MIT",
                        "license_url": f"https://github.com/example/test/blob/{commit}/LICENSE",
                        "provenance_class": "test-fixture",
                        "real_world_flight_verified": False,
                        "usage_note": "test",
                    }
                ],
                "safety_boundary": {
                    "explicit_download_only": True,
                    "offline_analysis_only": True,
                    "no_real_drone_connection": True,
                    "no_mavlink_command_execution": True,
                    "human_review_required": True,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    registry = load_open_source_log_registry(registry_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    target = cache_dir / "example_px4_mock.ulg"
    target.write_bytes(payload)

    verified = verify_cached_source(registry.sources[0], cache_dir)

    assert verified == target


def test_verify_cached_source_rejects_tampered_payload(tmp_path: Path) -> None:
    source_file = Path("data/sample_logs/example_px4_mock.ulg")
    payload = source_file.read_bytes()
    commit = "d" * 40
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "registry_id": "TEST-TAMPERED",
                "description": "test",
                "sources": [{
                    "source_id": "tampered-source",
                    "title": "test",
                    "repository": "example/test",
                    "commit": commit,
                    "source_path": "test/example_px4_mock.ulg",
                    "download_url": f"https://raw.githubusercontent.com/example/test/{commit}/test/example_px4_mock.ulg",
                    "filename": "example_px4_mock.ulg",
                    "format": "px4-ulog",
                    "size_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "license_spdx": "MIT",
                    "license_url": f"https://github.com/example/test/blob/{commit}/LICENSE",
                    "provenance_class": "test-fixture",
                    "real_world_flight_verified": False,
                    "usage_note": "test"
                }],
                "safety_boundary": {
                    "explicit_download_only": True,
                    "offline_analysis_only": True,
                    "no_real_drone_connection": True,
                    "no_mavlink_command_execution": True,
                    "human_review_required": True
                }
            }
        ),
        encoding="utf-8",
    )

    registry = load_open_source_log_registry(registry_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    target = cache_dir / "example_px4_mock.ulg"
    target.write_bytes(b"x" * len(payload))

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_cached_source(registry.sources[0], cache_dir)

    assert target.exists()
