from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_validate_handoff_package_cli_writes_validation_and_audit(tmp_path: Path) -> None:
    out_path = tmp_path / "handoff_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-handoff-package",
            "--package",
            "data/sample_handoff/organization_handoff_package.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Organization handoff package validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["findings"] == 0
    assert payload["human_review_required"] is True
    assert (tmp_path / "audit").exists()
