from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.drone_schemas import (
    BatteryAsset,
    DroneAsset,
    EvidenceRef,
    MissionPlan,
    PreflightCheckItem,
    PreflightCheckResult,
    PreflightObservation,
    Severity,
)


SKILL_NAME = "preflight-check"
SKILL_VERSION = "1.0.0"

def load_preflight_rules(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"输入文件不存在: {path}") from exc
    try:
        data = _parse_simple_yaml(text)
    except ValueError as exc:
        raise ValueError(f"YAML 规则文件格式无效: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"YAML 规则文件必须是对象: {path}")
    return data


def run_preflight_check(
    asset: DroneAsset,
    battery: BatteryAsset,
    mission: MissionPlan,
    observations: dict[str, Any],
    rules_path: Path,
) -> PreflightCheckResult:
    rules = load_preflight_rules(rules_path)
    blocking: list[PreflightCheckItem] = []
    warnings: list[PreflightCheckItem] = []
    observations_out: list[PreflightObservation] = []
    source = str(rules_path)
    obs_id = str(observations.get("observation_id", "preflight-observations"))

    def add(
        *,
        target: str,
        item: str,
        severity: Severity,
        reason: str,
        field: str,
        measured_value: float | int | str,
        threshold: float | int | str,
        rule_id: str,
        recommendation: str,
        source_type: str = "preflight",
        source_id: str | None = None,
    ) -> None:
        ref = EvidenceRef(
            source_type=source_type,
            source_id=source_id or f"{obs_id}:{field}",
            field=field,
            measured_value=measured_value,
            threshold=threshold,
            rule_id=rule_id,
            description=reason,
        )
        check = PreflightCheckItem(
            item=item,
            severity=severity,
            reason=reason,
            measured_value=measured_value,
            threshold=threshold,
            rule_id=rule_id,
            evidence_refs=[ref],
            recommendation=recommendation,
        )
        if target == "blocking":
            blocking.append(check)
        else:
            warnings.append(check)

    asset_rules = _section(rules, "asset")
    status = asset.operational_status
    if status in _list(asset_rules, "blocking_statuses"):
        add(
            target="blocking",
            item="asset_status",
            severity=Severity.CRITICAL,
            reason=f"无人机资产状态为 {status}，不允许作为离线建议放行。",
            field="operational_status",
            measured_value=status,
            threshold="active",
            rule_id="ASSET_STATUS_BLOCKING",
            recommendation="保持停飞并由运维负责人复核资产状态。",
            source_type="asset",
            source_id=asset.drone_id,
        )
    elif status in _list(asset_rules, "warning_statuses"):
        add(
            target="warning",
            item="asset_status",
            severity=Severity.MEDIUM,
            reason=f"无人机资产状态为 {status}，需要人工复核。",
            field="operational_status",
            measured_value=status,
            threshold="active",
            rule_id="ASSET_STATUS_REVIEW",
            recommendation="确认维护到期项是否已关闭后再决策。",
            source_type="asset",
            source_id=asset.drone_id,
        )

    maintenance_rules = _section(rules, "maintenance")
    high_items = _open_high_maintenance_items(asset)
    if high_items and bool(maintenance_rules.get("block_open_high_priority", True)):
        add(
            target="blocking",
            item="open_high_priority_maintenance",
            severity=Severity.CRITICAL,
            reason="存在未关闭的高优先级维护项。",
            field="open_maintenance_items",
            measured_value="; ".join(high_items),
            threshold="none",
            rule_id="OPEN_HIGH_PRIORITY_MAINTENANCE",
            recommendation="关闭高优先级维护项并记录复核结论后再进行飞行前决策。",
            source_type="asset",
            source_id=asset.drone_id,
        )

    battery_rules = _section(rules, "battery")
    _check_battery(add, battery, battery_rules)
    _check_observations(add, observations, _section(rules, "sensors"), _section(rules, "links"), obs_id)
    _check_mission(add, mission, battery, _section(rules, "mission"))

    for field in [
        "imu_status",
        "compass_status",
        "barometer_status",
        "gps_status",
        "rtk_status",
        "remote_control_link",
        "telemetry_link",
        "video_link",
        "network_link",
    ]:
        if field in observations:
            observations_out.append(
                PreflightObservation(
                    checklist_item=field,
                    observed_value=str(observations[field]),
                    drone_id=asset.drone_id,
                    human_review_required=False,
                    generated_by_skill=SKILL_NAME,
                    skill_version=SKILL_VERSION,
                )
            )

    status_value = "GO"
    if blocking:
        status_value = "NO_GO"
    elif warnings:
        status_value = "REVIEW_REQUIRED"

    evidence_refs = _unique_evidence([item for item in [*blocking, *warnings] for item in item.evidence_refs])
    if not evidence_refs:
        evidence_refs = [
            EvidenceRef(
                source_type="rules",
                source_id=source,
                field="preflight_status",
                measured_value="all_checks_passed",
                threshold="no_warning_or_blocking_items",
                rule_id="PREFLIGHT_ALL_CHECKS_PASS",
                description="离线飞行前检查未触发 warning 或 blocking 项。",
            )
        ]

    return PreflightCheckResult(
        status=status_value,
        observations=observations_out,
        blocking_items=blocking,
        warnings=warnings,
        evidence_refs=evidence_refs,
        human_review_required=status_value != "GO",
        drone_id=asset.drone_id,
        generated_by_skill=SKILL_NAME,
        skill_version=SKILL_VERSION,
    )


def _check_battery(add, battery: BatteryAsset, rules: dict[str, Any]) -> None:
    min_soc = _number(rules, "min_soc_pct")
    review_soc = _number(rules, "review_soc_pct")
    if battery.soc_pct < min_soc:
        add(
            target="blocking",
            item="battery_soc",
            severity=Severity.HIGH,
            reason=f"电池 SOC {battery.soc_pct}% 低于最低阈值。",
            field="soc_pct",
            measured_value=battery.soc_pct,
            threshold=min_soc,
            rule_id="BATTERY_SOC_BLOCKING",
            recommendation="更换或充电后重新执行飞行前检查。",
            source_type="battery",
            source_id=battery.battery_id,
        )
    elif battery.soc_pct < review_soc:
        add(
            target="warning",
            item="battery_soc",
            severity=Severity.MEDIUM,
            reason=f"电池 SOC {battery.soc_pct}% 低于复核阈值。",
            field="soc_pct",
            measured_value=battery.soc_pct,
            threshold=review_soc,
            rule_id="BATTERY_SOC_REVIEW",
            recommendation="确认任务余量，必要时更换电池。",
            source_type="battery",
            source_id=battery.battery_id,
        )

    min_voltage = _number(rules, "min_voltage_v")
    if battery.voltage_v is not None and battery.voltage_v < min_voltage:
        add(
            target="blocking",
            item="battery_voltage",
            severity=Severity.HIGH,
            reason=f"电池电压 {battery.voltage_v}V 低于最低阈值。",
            field="voltage_v",
            measured_value=battery.voltage_v,
            threshold=min_voltage,
            rule_id="BATTERY_VOLTAGE_BLOCKING",
            recommendation="更换电池并复测电压。",
            source_type="battery",
            source_id=battery.battery_id,
        )

    max_cycles = _number(rules, "max_cycle_count")
    review_cycles = _number(rules, "review_cycle_count")
    if battery.cycle_count > max_cycles:
        add(
            target="blocking",
            item="battery_cycle_count",
            severity=Severity.HIGH,
            reason=f"电池循环次数 {battery.cycle_count} 超过最大阈值。",
            field="cycle_count",
            measured_value=battery.cycle_count,
            threshold=max_cycles,
            rule_id="BATTERY_CYCLE_BLOCKING",
            recommendation="停止使用该电池并进行维护检测。",
            source_type="battery",
            source_id=battery.battery_id,
        )
    elif battery.cycle_count > review_cycles:
        add(
            target="warning",
            item="battery_cycle_count",
            severity=Severity.MEDIUM,
            reason=f"电池循环次数 {battery.cycle_count} 超过复核阈值。",
            field="cycle_count",
            measured_value=battery.cycle_count,
            threshold=review_cycles,
            rule_id="BATTERY_CYCLE_REVIEW",
            recommendation="复核电池健康状态和内阻记录。",
            source_type="battery",
            source_id=battery.battery_id,
        )

    min_temp = _number(rules, "min_temperature_c")
    max_temp = _number(rules, "max_temperature_c")
    if battery.temperature_c is not None and not min_temp <= battery.temperature_c <= max_temp:
        add(
            target="blocking",
            item="battery_temperature",
            severity=Severity.HIGH,
            reason=f"电池温度 {battery.temperature_c}C 超出允许范围。",
            field="temperature_c",
            measured_value=battery.temperature_c,
            threshold=f"{min_temp}..{max_temp}",
            rule_id="BATTERY_TEMPERATURE_BLOCKING",
            recommendation="将电池恢复到允许温度范围后再复查。",
            source_type="battery",
            source_id=battery.battery_id,
        )


def _check_observations(add, observations: dict[str, Any], sensor_rules: dict[str, Any], link_rules: dict[str, Any], obs_id: str) -> None:
    sensor_fields = ["imu_status", "compass_status", "barometer_status", "gps_status", "rtk_status"]
    link_fields = ["remote_control_link", "telemetry_link", "video_link", "network_link"]
    for field in sensor_fields:
        _check_status_field(add, observations, field, sensor_rules, "sensor", obs_id)
    for field in link_fields:
        _check_status_field(add, observations, field, link_rules, "link", obs_id)

    min_satellites = _number(sensor_rules, "min_gps_satellites")
    gps_satellites = observations.get("gps_satellites")
    if isinstance(gps_satellites, (int, float)) and gps_satellites < min_satellites:
        add(
            target="blocking",
            item="gps_satellites",
            severity=Severity.HIGH,
            reason=f"GPS 卫星数 {gps_satellites} 低于阈值。",
            field="gps_satellites",
            measured_value=gps_satellites,
            threshold=min_satellites,
            rule_id="GPS_SATELLITES_BLOCKING",
            recommendation="等待定位质量恢复或更换起飞环境后复查。",
            source_id=f"{obs_id}:gps_satellites",
        )

    max_hdop = _number(sensor_rules, "max_gps_hdop")
    gps_hdop = observations.get("gps_hdop")
    if isinstance(gps_hdop, (int, float)) and gps_hdop > max_hdop:
        add(
            target="warning",
            item="gps_hdop",
            severity=Severity.MEDIUM,
            reason=f"GPS HDOP {gps_hdop} 高于复核阈值。",
            field="gps_hdop",
            measured_value=gps_hdop,
            threshold=max_hdop,
            rule_id="GPS_HDOP_REVIEW",
            recommendation="复核定位质量，必要时调整任务窗口。",
            source_id=f"{obs_id}:gps_hdop",
        )


def _check_status_field(add, observations: dict[str, Any], field: str, rules: dict[str, Any], category: str, obs_id: str) -> None:
    if field not in observations:
        add(
            target="blocking",
            item=field,
            severity=Severity.HIGH,
            reason=f"{field} 缺失。",
            field=field,
            measured_value="missing",
            threshold="ok",
            rule_id=f"{field.upper()}_MISSING",
            recommendation="补齐飞行前观测数据后重新检查。",
            source_id=f"{obs_id}:{field}",
        )
        return
    value = str(observations[field]).lower()
    if value in _list(rules, "blocking_values"):
        add(
            target="blocking",
            item=field,
            severity=Severity.HIGH,
            reason=f"{category} 状态 {field}={observations[field]} 阻断飞行前放行建议。",
            field=field,
            measured_value=str(observations[field]),
            threshold="ok",
            rule_id=f"{field.upper()}_BLOCKING",
            recommendation="排除该项异常并由人工复核后再运行检查。",
            source_id=f"{obs_id}:{field}",
        )
    elif value in _list(rules, "warning_values"):
        add(
            target="warning",
            item=field,
            severity=Severity.MEDIUM,
            reason=f"{category} 状态 {field}={observations[field]} 需要人工复核。",
            field=field,
            measured_value=str(observations[field]),
            threshold="ok",
            rule_id=f"{field.upper()}_REVIEW",
            recommendation="确认链路或传感器状态稳定后再决策。",
            source_id=f"{obs_id}:{field}",
        )


def _check_mission(add, mission: MissionPlan, battery: BatteryAsset, rules: dict[str, Any]) -> None:
    max_rth = _number(rules, "max_return_to_home_altitude_m")
    if mission.return_to_home_altitude_m is not None and mission.return_to_home_altitude_m > max_rth:
        add(
            target="warning",
            item="return_to_home_altitude",
            severity=Severity.MEDIUM,
            reason=f"返航高度 {mission.return_to_home_altitude_m}m 高于复核阈值。",
            field="return_to_home_altitude_m",
            measured_value=mission.return_to_home_altitude_m,
            threshold=max_rth,
            rule_id="MISSION_RTH_ALTITUDE_REVIEW",
            recommendation="复核任务高度约束和现场障碍物条件。",
            source_type="mission",
            source_id=mission.mission_id,
        )

    max_distance = _number(rules, "max_planned_distance_km")
    if mission.planned_distance_km is not None and mission.planned_distance_km > max_distance:
        add(
            target="blocking",
            item="planned_distance",
            severity=Severity.HIGH,
            reason=f"计划航程 {mission.planned_distance_km}km 超过规则阈值。",
            field="planned_distance_km",
            measured_value=mission.planned_distance_km,
            threshold=max_distance,
            rule_id="MISSION_DISTANCE_BLOCKING",
            recommendation="缩短任务或拆分任务后重新评估。",
            source_type="mission",
            source_id=mission.mission_id,
        )

    max_time = _number(rules, "max_estimated_flight_time_min")
    if mission.estimated_flight_time_min is not None and mission.estimated_flight_time_min > max_time:
        add(
            target="warning",
            item="estimated_flight_time",
            severity=Severity.MEDIUM,
            reason=f"预计飞行时间 {mission.estimated_flight_time_min} 分钟高于复核阈值。",
            field="estimated_flight_time_min",
            measured_value=mission.estimated_flight_time_min,
            threshold=max_time,
            rule_id="MISSION_TIME_REVIEW",
            recommendation="复核任务时间和电池余量。",
            source_type="mission",
            source_id=mission.mission_id,
        )

    reserve = mission.required_battery_reserve_pct
    minimum_reserve = _number(rules, "min_battery_reserve_pct")
    if reserve is not None and reserve < minimum_reserve:
        add(
            target="warning",
            item="battery_reserve",
            severity=Severity.MEDIUM,
            reason=f"任务电池余量要求 {reserve}% 低于规则阈值。",
            field="required_battery_reserve_pct",
            measured_value=reserve,
            threshold=minimum_reserve,
            rule_id="MISSION_RESERVE_REVIEW",
            recommendation="提高任务余量或缩短任务。",
            source_type="mission",
            source_id=mission.mission_id,
        )
    elif reserve is not None and battery.soc_pct < reserve:
        add(
            target="blocking",
            item="battery_reserve",
            severity=Severity.HIGH,
            reason=f"电池 SOC {battery.soc_pct}% 低于任务要求余量 {reserve}%。",
            field="soc_pct",
            measured_value=battery.soc_pct,
            threshold=reserve,
            rule_id="MISSION_BATTERY_RESERVE_BLOCKING",
            recommendation="更换电池或调整任务后重新检查。",
            source_type="battery",
            source_id=battery.battery_id,
        )


def _open_high_maintenance_items(asset: DroneAsset) -> list[str]:
    items: list[str] = []
    for item in asset.open_maintenance_items:
        priority = str(item.get("priority", "")).upper()
        status = str(item.get("status", "open")).lower()
        if priority in {"HIGH", "CRITICAL"} and status not in {"closed", "resolved"}:
            items.append(str(item.get("description", item)))
    for item in asset.maintenance_history:
        text = item.upper()
        if "OPEN HIGH" in text or "OPEN CRITICAL" in text:
            items.append(item)
    return items


def _unique_evidence(refs: list[EvidenceRef]) -> list[EvidenceRef]:
    result: list[EvidenceRef] = []
    seen: set[tuple[str, str, str]] = set()
    for ref in refs:
        key = (ref.source_id, ref.field, ref.rule_id)
        if key not in seen:
            result.append(ref)
            seen.add(key)
    return result


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} 必须是对象")
    return value


def _number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} 必须是数字")
    return float(value)


def _list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} 必须是列表")
    return [str(item).lower() for item in value]


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"无法解析行: {raw_line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"缩进无效: {raw_line}")
        parent = stack[-1][1]
        if raw_value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(raw_value)
    return root


def _parse_scalar(value: str) -> Any:
    value = value.split(" #", 1)[0].strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value
