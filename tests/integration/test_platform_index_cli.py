from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file, write_json


runner = CliRunner()


def test_validate_platform_index_cli_writes_validation_and_audit(tmp_path: Path) -> None:
    out_path = tmp_path / "platform_index_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-platform-index",
            "--index",
            "data/sample_platform/platform_readiness_index.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Platform readiness index validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["findings"] == 0
    assert payload["human_review_required"] is True
    assert (tmp_path / "audit").exists()


def test_validate_platform_index_cli_returns_nonzero_for_review_required(tmp_path: Path) -> None:
    index = read_json_file(Path("data/sample_platform/platform_readiness_index.json"))
    assert isinstance(index, dict)
    index["safety_boundary"]["offline_only"] = False
    index_path = tmp_path / "platform_readiness_index.json"
    out_path = tmp_path / "platform_index_validation.json"
    write_json(index_path, index)

    result = runner.invoke(
        app,
        ["validate-platform-index", "--index", str(index_path), "--out", str(out_path)],
    )

    assert result.exit_code == 1
    assert "requires review" in result.output
    assert read_json_file(out_path)["status"] == "REVIEW_REQUIRED"
    audit_paths = list((tmp_path / "audit").glob("platform-readiness-index-validation-*.json"))
    assert len(audit_paths) == 1
    assert read_json_file(audit_paths[0])["status"] == "review_required"
