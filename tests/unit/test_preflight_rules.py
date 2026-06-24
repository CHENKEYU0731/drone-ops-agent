from pathlib import Path

from packages.drone_schemas import BatteryAsset, DroneAsset, MissionPlan, load_model, read_json_file
from packages.preflight_rules import run_preflight_check


RULES = Path("data/sample_rules/preflight_rules.yaml")


def _asset(status: str = "active", maintenance: list[str] | None = None) -> DroneAsset:
    return DroneAsset(
        drone_id="UAV-001",
        model="Quad-X4",
        serial_number="SN-UAV-001",
        firmware_version="simulated-1.0",
        total_flight_hours=42.5,
        battery_ids=["BAT-001"],
        maintenance_history=maintenance or ["2026-06-12: routine inspection closed"],
        operational_status=status,
    )


def _battery(**overrides) -> BatteryAsset:
    data = {
        "battery_id": "BAT-001",
        "nominal_voltage_v": 15.2,
        "cycle_count": 80,
        "health_pct": 96,
        "soc_pct": 92,
        "voltage_v": 16.4,
        "temperature_c": 28,
    }
    data.update(overrides)
    return BatteryAsset(**data)


def _mission(**overrides) -> MissionPlan:
    data = {
        "mission_id": "MISSION-001",
        "drone_id": "UAV-001",
        "planned_start": "2026-06-24T10:00:00Z",
        "planned_end": "2026-06-24T10:10:00Z",
        "expected_modes": ["STABILIZE", "AUTO", "LAND"],
        "max_planned_altitude_m": 60,
        "return_to_home_altitude_m": 45,
        "planned_distance_km": 1.2,
        "estimated_flight_time_min": 8,
        "required_battery_reserve_pct": 30,
    }
    data.update(overrides)
    return MissionPlan.model_validate(data)


def _observations(**overrides) -> dict:
    data = {
        "observation_id": "OBS-OK",
        "imu_status": "ok",
        "compass_status": "ok",
        "barometer_status": "ok",
        "gps_status": "ok",
        "rtk_status": "ok",
        "gps_satellites": 18,
        "gps_hdop": 0.8,
        "remote_control_link": "ok",
        "telemetry_link": "ok",
        "video_link": "ok",
        "network_link": "ok",
    }
    data.update(overrides)
    return data


def test_preflight_go_case_has_no_review_requirement() -> None:
    result = run_preflight_check(_asset(), _battery(), _mission(), _observations(), RULES)

    assert result.status == "GO"
    assert result.human_review_required is False
    assert result.blocking_items == []
    assert result.warnings == []
    assert result.evidence_refs


def test_preflight_warning_case_requires_review_and_evidence() -> None:
    result = run_preflight_check(
        _asset("maintenance_due"),
        _battery(cycle_count=210),
        _mission(),
        _observations(remote_control_link="degraded"),
        RULES,
    )

    assert result.status == "REVIEW_REQUIRED"
    assert result.human_review_required is True
    assert result.blocking_items == []
    assert result.warnings
    assert all(item.evidence_refs for item in result.warnings)
    assert all(item.rule_id for item in result.warnings)


def test_preflight_blocking_case_returns_no_go() -> None:
    result = run_preflight_check(
        _asset("grounded", maintenance=["OPEN HIGH: battery connector overheating"]),
        _battery(soc_pct=18, voltage_v=13.9, temperature_c=51),
        _mission(planned_distance_km=9.5),
        _observations(imu_status="fail", telemetry_link="fail"),
        RULES,
    )

    assert result.status == "NO_GO"
    assert result.human_review_required is True
    assert result.blocking_items
    assert all(item.evidence_refs for item in result.blocking_items)
    assert {item.severity for item in result.blocking_items} <= {"HIGH", "CRITICAL"}


def test_blocking_items_take_precedence_over_warnings() -> None:
    result = run_preflight_check(
        _asset("maintenance_due"),
        _battery(soc_pct=18, cycle_count=210),
        _mission(),
        _observations(remote_control_link="degraded"),
        RULES,
    )

    assert result.blocking_items
    assert result.warnings
    assert result.status == "NO_GO"


def test_repository_samples_cover_go_review_and_no_go() -> None:
    asset = load_model(Path("data/sample_assets/uav_001.json"), DroneAsset)
    mission = load_model(Path("data/sample_missions/example_mission.json"), MissionPlan)

    ok = run_preflight_check(
        asset,
        load_model(Path("data/sample_assets/battery_001.json"), BatteryAsset),
        mission,
        read_json_file(Path("data/sample_missions/preflight_observations_ok.json")),
        RULES,
    )
    review = run_preflight_check(
        asset,
        load_model(Path("data/sample_assets/battery_degraded.json"), BatteryAsset),
        mission,
        read_json_file(Path("data/sample_missions/preflight_observations_warning.json")),
        RULES,
    )
    no_go = run_preflight_check(
        asset,
        load_model(Path("data/sample_assets/battery_001.json"), BatteryAsset),
        mission,
        read_json_file(Path("data/sample_missions/preflight_observations_blocking.json")),
        RULES,
    )

    assert ok.status == "GO"
    assert review.status == "REVIEW_REQUIRED"
    assert no_go.status == "NO_GO"


def test_sensor_and_link_status_rules_are_loaded_from_yaml(tmp_path: Path) -> None:
    rules = tmp_path / "rules.yaml"
    rules.write_text(
        """
asset:
  blocking_statuses: [grounded]
  warning_statuses: [maintenance_due]
battery:
  min_soc_pct: 25
  review_soc_pct: 40
  min_voltage_v: 14.4
  review_cycle_count: 200
  max_cycle_count: 300
  min_temperature_c: 0
  max_temperature_c: 45
sensors:
  blocking_values: [configured_block]
  warning_values: [configured_warn]
  min_gps_satellites: 8
  max_gps_hdop: 2.0
links:
  blocking_values: [configured_block]
  warning_values: [configured_warn]
mission:
  max_return_to_home_altitude_m: 80
  max_planned_distance_km: 5
  max_estimated_flight_time_min: 18
  min_battery_reserve_pct: 25
maintenance:
  block_open_high_priority: true
""".strip(),
        encoding="utf-8",
    )

    result = run_preflight_check(
        _asset(),
        _battery(),
        _mission(),
        _observations(imu_status="fail", telemetry_link="degraded"),
        rules,
    )

    assert result.status == "GO"
