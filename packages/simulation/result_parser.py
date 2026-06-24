from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from packages.drone_schemas import read_json_file


class SimulationResult(BaseModel):
    result_id: str
    scenario_id: str
    mission_id: str | None = None
    source: str = "offline_mock_export"
    duration_s: float = Field(ge=0)
    completed: bool
    max_altitude_m: float = Field(ge=0)
    max_cross_track_error_m: float = Field(ge=0)
    max_altitude_error_m: float = Field(ge=0)
    failsafe_events: list[str] = Field(default_factory=list)
    failure_events: list[str] = Field(default_factory=list)
    energy_remaining_pct: float = Field(ge=0, le=100)
    timeout: bool = False
    constraints: dict[str, float] = Field(default_factory=dict)


def parse_simulation_result(path: Path) -> SimulationResult:
    data = read_json_file(path)
    if not isinstance(data, dict):
        raise ValueError(f"仿真结果 JSON 必须是对象: {path}")
    try:
        return SimulationResult.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"仿真结果 schema 无效: {path}: {exc}") from exc
