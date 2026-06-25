from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from packages.log_parsers import parse_flight_log_details


REAL_FIXTURE = Path("data/sample_logs/px4/real_sample.ulg")


class _FakeDataset:
    def __init__(self, name: str, rows: list[dict[str, object]]) -> None:
        self.name = name
        fields = rows[0].keys() if rows else []
        self.data = {field: [row.get(field) for row in rows] for field in fields}


class _FakeULog:
    def __init__(self, path: str) -> None:
        assert path.endswith(".ulg")
        self.data_list = [
            _FakeDataset("battery_status", [{"timestamp": 1_000_000, "voltage_v": 16.2, "current_a": 12.5, "remaining": 0.82}]),
            _FakeDataset("vehicle_status", [{"timestamp": 1_000_000, "nav_state": "POSCTL"}]),
            _FakeDataset("vehicle_local_position", [{"timestamp": 1_000_000, "z": -23.4}]),
            _FakeDataset("vehicle_gps_position", [{"timestamp": 1_000_000, "satellites_used": 11, "hdop": 0.9}]),
            _FakeDataset(
                "vehicle_imu_status",
                [{"timestamp": 1_000_000, "accel_vibration_metric": 0.2, "gyro_vibration_metric": 0.3, "delta_angle_coning_metric": 0.4}],
            ),
            _FakeDataset("actuator_outputs", [{"timestamp": 1_000_000, "outputs": [0.31, 0.32, 0.33, 0.34]}]),
            _FakeDataset("telemetry_status", [{"timestamp": 1_000_000, "rssi": 88.0}]),
            _FakeDataset("sensor_combined", [{"timestamp": 1_000_000, "temperature": 36.5}]),
        ]


def test_missing_px4_real_fixture_is_documented_skip() -> None:
    if not REAL_FIXTURE.exists():
        pytest.skip("Optional real PX4 ULog fixture not present; see data/sample_logs/px4/README.md")

    parsed = parse_flight_log_details(REAL_FIXTURE, requested_format="auto")

    assert parsed.actual_format == "px4-ulog"
    assert parsed.records
    assert parsed.parser_metadata["mock_fixture"] is False


def test_px4_pyulog_path_records_sample_count_and_topics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = tmp_path / "redacted.ulg"
    fixture.write_bytes(b"ULog fake binary")
    fake_module = types.SimpleNamespace(ULog=_FakeULog)
    monkeypatch.setitem(sys.modules, "pyulog", fake_module)
    monkeypatch.setattr("packages.log_parsers.px4_ulog.find_spec", lambda name: object() if name == "pyulog" else None)

    parsed = parse_flight_log_details(fixture, requested_format="px4-ulog")

    assert len(parsed.records) == 1
    assert parsed.records[0].battery_soc_pct == 82
    assert parsed.records[0].motor_4_output == 34
    assert parsed.parser_metadata["mock_fixture"] is False
    assert parsed.parser_metadata["sample_count"] == 1
    assert "battery_status" in parsed.parser_metadata["topics_used"]


def test_px4_missing_required_topic_error_names_topic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class MissingBatteryULog:
        def __init__(self, path: str) -> None:
            self.data_list = [_FakeDataset("vehicle_status", [{"timestamp": 1_000_000, "nav_state": "POSCTL"}])]

    fixture = tmp_path / "missing-topic.ulg"
    fixture.write_bytes(b"ULog fake binary")
    monkeypatch.setitem(sys.modules, "pyulog", types.SimpleNamespace(ULog=MissingBatteryULog))
    monkeypatch.setattr("packages.log_parsers.px4_ulog.find_spec", lambda name: object() if name == "pyulog" else None)

    with pytest.raises(ValueError, match="battery_status"):
        parse_flight_log_details(fixture, requested_format="px4-ulog")
