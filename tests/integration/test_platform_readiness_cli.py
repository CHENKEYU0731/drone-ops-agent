from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app
from packages.drone_schemas import read_json_file


runner = CliRunner()


def test_build_report_bundle_cli_writes_manifest_and_audit(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "run-mvp",
            "--log",
            "data/sample_logs/example_flight.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(report_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["validate-report", "--report-dir", str(report_dir), "--write-index"])
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "report_bundle_manifest.json"
    result = runner.invoke(
        app,
        [
            "build-report-bundle",
            "--report-dir",
            str(report_dir),
            "--workspace-project-id",
            "workspace-local-demo",
            "--bundle-id",
            "bundle-cli-test",
            "--drone-id",
            "UAV-001",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["bundle_id"] == "bundle-cli-test"
    assert payload["human_review_required"] is True
    assert payload["safety_boundary"]["no_external_upload"] is True
    assert "ops_report.md" in payload["file_refs"]


def test_validate_platform_readiness_cli_writes_validation_output(tmp_path: Path) -> None:
    out_path = tmp_path / "platform_readiness_validation.json"

    result = runner.invoke(
        app,
        [
            "validate-platform-readiness",
            "--workspace",
            "data/sample_platform/workspace_project.json",
            "--bundle",
            "data/sample_platform/report_bundle_manifest.json",
            "--checklist",
            "data/sample_platform/platform_readiness_checklist.json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Platform readiness validation passed" in result.output
    payload = read_json_file(out_path)
    assert isinstance(payload, dict)
    assert payload["status"] == "PASS"
    assert payload["human_review_required"] is True
