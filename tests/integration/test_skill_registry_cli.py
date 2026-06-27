from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_list_skills_cli_writes_skill_registry(tmp_path: Path) -> None:
    out_path = tmp_path / "skill_registry.json"

    result = runner.invoke(
        app,
        [
            "list-skills",
            "--rule-pack",
            "data/sample_rule_packs/offline_default_rules.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["registry_id"] == "SKILL-REGISTRY-OFFLINE"
    assert payload["rule_packs"][0]["rule_pack_id"] == "offline-default-rules"
    assert payload["safety_boundary"]["advisory_only"] is True


def test_list_rule_packs_cli_writes_known_rule_packs(tmp_path: Path) -> None:
    out_path = tmp_path / "rule_packs.json"

    result = runner.invoke(
        app,
        [
            "list-rule-packs",
            "--rule-pack",
            "data/sample_rule_packs/offline_default_rules.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["rule_packs"] == [
        {
            "rule_pack_id": "offline-default-rules",
            "version": "1.3.0",
            "path": "data/sample_rule_packs/offline_default_rules.json",
        }
    ]
