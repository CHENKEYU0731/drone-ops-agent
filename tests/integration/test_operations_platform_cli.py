from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file, write_json


runner = CliRunner()


def test_validate_operations_platform_cli_writes_validation_and_audit(tmp_path: Path) -> None:
    out_path = tmp_path / "operations_platform_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-operations-platform",
            "--baseline",
            "data/sample_platform/operations_platform_baseline.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Operations platform baseline validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["findings"] == 0
    assert payload["human_review_required"] is True
    assert (tmp_path / "audit").exists()


def test_validate_operations_platform_cli_returns_nonzero_for_review_required(tmp_path: Path) -> None:
    baseline = read_json_file(Path("data/sample_platform/operations_platform_baseline.json"))
    assert isinstance(baseline, dict)
    baseline["modules"] = []
    baseline_path = tmp_path / "operations_platform_baseline.json"
    out_path = tmp_path / "operations_platform_validation.json"
    write_json(baseline_path, baseline)

    result = runner.invoke(
        app,
        ["validate-operations-platform", "--baseline", str(baseline_path), "--out", str(out_path)],
    )

    assert result.exit_code == 1
    assert "requires review" in result.output
    assert read_json_file(out_path)["status"] == "REVIEW_REQUIRED"
    audit_paths = list((tmp_path / "audit").glob("operations-platform-validation-*.json"))
    assert len(audit_paths) == 1
    assert read_json_file(audit_paths[0])["status"] == "review_required"
