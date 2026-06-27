from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_validate_adapters_cli_writes_validation_and_audit(tmp_path: Path) -> None:
    out_path = tmp_path / "adapter_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-adapters",
            "--registry",
            "data/sample_adapters/offline_adapter_registry.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Adapter registry validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["adapters"] == 3
    assert payload["counts"]["findings"] == 0
    assert payload["human_review_required"] is True
    assert (tmp_path / "audit").exists()


def test_validate_approvals_cli_writes_validation_and_audit(tmp_path: Path) -> None:
    out_path = tmp_path / "approval_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-approvals",
            "--packet",
            "data/sample_approvals/approval_packet.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Approval workflow validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["approvals"] == 2
    assert payload["counts"]["findings"] == 0
    assert payload["human_review_required"] is True
    assert (tmp_path / "audit").exists()
