from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_validate_datasets_cli_writes_validation_output(tmp_path: Path) -> None:
    out_path = tmp_path / "dataset_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-datasets",
            "--registry",
            "data/sample_datasets/registry.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Dataset registry validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["findings"] == 0
    assert payload["human_review_required"] is True
    assert payload["safety_boundary"]["advisory_only"] is True
