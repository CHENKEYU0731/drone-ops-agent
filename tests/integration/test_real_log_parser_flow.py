from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from apps.cli.main import app


runner = CliRunner()


def test_placeholder_real_fixture_paths_are_documented() -> None:
    assert Path("data/sample_logs/README.md").exists()
    assert Path("data/sample_logs/px4/README.md").exists()
    assert Path("data/sample_logs/ardupilot/README.md").exists()


def test_mock_ulog_and_bin_still_pass_auto_format(tmp_path: Path) -> None:
    cases = [
        ("data/sample_logs/example_px4_mock.ulg", "px4-ulog"),
        ("data/sample_logs/example_ardupilot.bin", "ardupilot-bin"),
    ]
    for log_path, expected_format in cases:
        out_dir = tmp_path / expected_format
        result = runner.invoke(
            app,
            [
                "analyze-log",
                "--log",
                log_path,
                "--asset",
                "data/sample_assets/uav_001.json",
                "--out",
                str(out_dir),
                "--format",
                "auto",
            ],
        )

        assert result.exit_code == 0, result.output
        assert (out_dir / "flight_summary.json").exists()
        assert (out_dir / "anomalies.json").exists()
        assert list((out_dir / "audit").glob("flight-log-analysis-*.json"))


@pytest.mark.parametrize(
    ("fixture", "expected_hint"),
    [
        (Path("data/sample_logs/px4/real_sample.ulg"), "data/sample_logs/px4/README.md"),
        (Path("data/sample_logs/ardupilot/real_sample.bin"), "data/sample_logs/ardupilot/README.md"),
    ],
)
def test_optional_real_fixtures_are_skipped_when_absent(fixture: Path, expected_hint: str) -> None:
    if not fixture.exists():
        pytest.skip(f"Optional real fixture not present; see {expected_hint}")

    out_dir = fixture.parent / "_validation_output"
    result = runner.invoke(
        app,
        [
            "analyze-log",
            "--log",
            str(fixture),
            "--asset",
            "data/sample_assets/uav_001.json",
            "--out",
            str(out_dir),
            "--format",
            "auto",
        ],
    )

    assert result.exit_code == 0, result.output
