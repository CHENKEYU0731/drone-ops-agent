import json
from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_preflight_cli_writes_result_and_audit(tmp_path: Path) -> None:
    out_dir = tmp_path / "preflight"
    result = runner.invoke(
        app,
        [
            "preflight-check",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--battery",
            "data/sample_assets/battery_001.json",
            "--mission",
            "data/sample_missions/example_mission.json",
            "--observations",
            "data/sample_missions/preflight_observations_ok.json",
            "--rules",
            "data/sample_rules/preflight_rules.yaml",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    output = out_dir / "preflight_check_result.json"
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "GO"
    assert payload["human_review_required"] is True

    audit_files = list((out_dir / "audit").glob("preflight-check-*.json"))
    assert audit_files
    audit = json.loads(audit_files[0].read_text(encoding="utf-8"))
    assert audit["skill_name"] == "preflight-check"
    assert audit["output_refs"] == [str(output)]
    assert audit["status"] == "success"


def test_preflight_cli_missing_file_error_is_clear(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "preflight-check",
            "--asset",
            "missing_asset.json",
            "--battery",
            "data/sample_assets/battery_001.json",
            "--mission",
            "data/sample_missions/example_mission.json",
            "--observations",
            "data/sample_missions/preflight_observations_ok.json",
            "--rules",
            "data/sample_rules/preflight_rules.yaml",
            "--out",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "missing_asset.json" in result.output
    assert "Traceback" not in result.output
