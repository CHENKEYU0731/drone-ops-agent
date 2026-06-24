from pathlib import Path

from typer.testing import CliRunner

from apps.cli.main import app


def test_run_mvp_generates_full_output_set(tmp_path: Path) -> None:
    out_dir = tmp_path / "mvp"
    result = CliRunner().invoke(
        app,
        [
            "run-mvp",
            "--log",
            "data/sample_logs/example_flight.csv",
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    for filename in [
        "flight_summary.json",
        "anomalies.json",
        "diagnosis.json",
        "maintenance_recommendations.json",
        "ops_report.md",
    ]:
        assert (out_dir / filename).exists()
    assert list((out_dir / "audit").glob("*.json"))
