from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from packages.log_parsers import parse_flight_log_details


REAL_FIXTURE = Path("data/sample_logs/px4/real_sample.ulg")


class _FakeDataset:
    def __init__(self, name: str, rows: list[dict[str, object]], multi_id: int = 0) -> None:
        self.name = name
        self.multi_id = multi_id
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


def test_px4_upstream_field_names_are_mapped_without_mock_only_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UpstreamULog:
        def __init__(self, path: str) -> None:
            self.data_list = [
                _FakeDataset(
                    "battery_status",
                    [{"timestamp": 1_000_000, "voltage_v": 15.8, "current_a": 18.0, "remaining": 0.64, "temperature": 33.0}],
                ),
                _FakeDataset(
                    "battery_status",
                    [{"timestamp": 1_000_000, "voltage_v": 0.0, "current_a": 0.0, "remaining": 0.0}],
                    multi_id=1,
                ),
                _FakeDataset("vehicle_status", [{"timestamp": 1_000_000, "nav_state": 3}]),
                _FakeDataset("vehicle_local_position", [{"timestamp": 1_000_000, "z": -18.0}]),
                _FakeDataset("vehicle_gps_position", [{"timestamp": 1_000_000, "satellites_used": 12, "eph": 0.8}]),
                _FakeDataset(
                    "vehicle_imu_status",
                    [{"timestamp": 1_000_000, "accel_vibration_metric": 0.1, "gyro_vibration_metric": 0.2, "gyro_coning_vibration": 0.3}],
                ),
                _FakeDataset(
                    "actuator_outputs",
                    [{"timestamp": 1_000_000, "output[0]": 1200, "output[1]": 1300, "output[2]": 1400, "output[3]": 1500}],
                ),
                _FakeDataset("telemetry_status", [{"timestamp": 1_000_000, "rx_message_lost_rate": 0.07}]),
                _FakeDataset("sensor_combined", [{"timestamp": 1_000_000, "gyro_rad[0]": 0.0}]),
                _FakeDataset("sensor_baro", [{"timestamp": 1_000_000, "temperature": 35.5}]),
            ]

    fixture = tmp_path / "upstream.ulg"
    fixture.write_bytes(b"ULog upstream binary")
    monkeypatch.setitem(sys.modules, "pyulog", types.SimpleNamespace(ULog=UpstreamULog))
    monkeypatch.setattr("packages.log_parsers.px4_ulog.find_spec", lambda name: object() if name == "pyulog" else None)

    parsed = parse_flight_log_details(fixture, requested_format="px4-ulog")

    record = parsed.records[0]
    assert record.battery_voltage_v == 15.8
    assert [record.motor_1_output, record.motor_2_output, record.motor_3_output, record.motor_4_output] == [20, 30, 40, 50]
    assert record.link_quality_pct == 93
    assert record.temperature_c == 35.5
    assert record.vibration_z == 0.3
    assert parsed.parser_metadata["topic_instances"]["battery_status"] == [0, 1]
    assert parsed.parser_metadata["timestamp_basis"] == "boot-relative-microseconds-mapped-to-unix-epoch"
    assert any("actuator outputs" in warning for warning in parsed.warnings)
