import hashlib
import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def _fixture_registry(tmp_path: Path) -> tuple[Path, Path]:
    source = Path("data/sample_logs/example_px4_mock.ulg")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    shutil.copyfile(source, cache_dir / source.name)
    payload = source.read_bytes()
    commit = "c" * 40
    registry = {
        "schema_version": 1,
        "registry_id": "CLI-TEST",
        "description": "test",
        "sources": [{
            "source_id": "cli-test-log",
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
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return registry_path, cache_dir


def test_open_source_log_validation_and_case_study_cli(tmp_path: Path) -> None:
    registry_path, cache_dir = _fixture_registry(tmp_path)
    validation_path = tmp_path / "registry_validation.json"
    result = runner.invoke(app, ["validate-open-log-registry", "--registry", str(registry_path), "--out", str(validation_path)])
    assert result.exit_code == 0, result.output
    validation = read_json_file(validation_path)
    assert isinstance(validation, dict) and validation["status"] == "PASS"

    out_dir = tmp_path / "case-study"
    result = runner.invoke(
        app,
        [
            "run-open-log-case-studies",
            "--registry",
            str(registry_path),
            "--cache-dir",
            str(cache_dir),
            "--drone-id",
            "UAV-TEST",
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = read_json_file(out_dir / "open_log_case_study.json")
    assert isinstance(payload, dict) and payload["status"] == "PASS"
    assert (out_dir / "open_log_case_study.md").exists()
    assert list((out_dir / "audit").glob("open-source-log-case-study-*.json"))
