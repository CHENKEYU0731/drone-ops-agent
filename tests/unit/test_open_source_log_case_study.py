import hashlib
import json
import shutil
from pathlib import Path

from packages.open_source_logs import run_open_source_log_case_study


def _write_registry(tmp_path: Path) -> tuple[Path, Path]:
    source = Path("data/sample_logs/example_px4_mock.ulg")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    target = cache_dir / source.name
    shutil.copyfile(source, target)
    payload = source.read_bytes()
    commit = "b" * 40
    registry = {
        "schema_version": 1,
        "registry_id": "TEST-CASE-STUDY",
        "description": "test",
        "sources": [
            {
                "source_id": "test-px4-log",
                "title": "test",
                "repository": "example/test",
                "commit": commit,
                "source_path": f"test/{source.name}",
                "download_url": f"https://raw.githubusercontent.com/example/test/{commit}/test/{source.name}",
                "filename": source.name,
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
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry_path, cache_dir


def test_open_source_log_case_study_is_deterministic_and_candid(tmp_path: Path) -> None:
    registry_path, cache_dir = _write_registry(tmp_path)

    first = run_open_source_log_case_study(registry_path, cache_dir, "UAV-TEST")
    second = run_open_source_log_case_study(registry_path, cache_dir, "UAV-TEST")

    assert first == second
    assert first["status"] == "PASS"
    assert first["case_count"] == 1
    assert first["cases"][0]["record_count"] == 3
    assert first["cases"][0]["real_world_flight_verified"] is False
    assert "不是真实场景异常检测准确率" in first["limitations"][-1]
    assert len(first["result_digest"]) == 64
