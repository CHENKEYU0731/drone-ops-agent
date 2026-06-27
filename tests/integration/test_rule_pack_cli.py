from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_validate_rule_pack_cli_writes_validation_output(tmp_path: Path) -> None:
    out_path = tmp_path / "rule_pack_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-rule-pack",
            "--rule-pack",
            "data/sample_rule_packs/offline_default_rules.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["counts"]["rules"] == 4
    assert payload["rule_pack"]["pack_id"] == "offline-default-rules"
    assert payload["safety_boundary"]["advisory_only"] is True
