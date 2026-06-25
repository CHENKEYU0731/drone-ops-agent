from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel, Field, ValidationError

from packages.drone_schemas import SimulationScenario, read_json_file
from packages.simulation.result_parser import SimulationResult


INVALID_INPUT = "INVALID_INPUT"
SUPPORTED_EXPECTED_RESULTS = {"PASS", "FAIL", "REVIEW_REQUIRED", INVALID_INPUT}


class SimulationScenarioMatrixCase(BaseModel):
    case_id: str
    description: str
    expected_result: str
    mode: str = "offline_mock_import"
    safety_boundary: str = "advisory_only"
    expected_error_contains: str | None = None
    scenario: dict[str, Any]
    result: dict[str, Any]

    def validate_payloads(self) -> tuple[SimulationScenario, SimulationResult]:
        try:
            scenario = SimulationScenario.model_validate(self.scenario)
            result = SimulationResult.model_validate(self.result)
        except ValidationError as exc:
            message = "invalid simulation matrix payload"
            if self.expected_error_contains:
                message = self.expected_error_contains
            raise ValueError(message) from exc

        if scenario.scenario_id != result.scenario_id:
            message = self.expected_error_contains or "simulation scenario_id mismatch"
            raise ValueError(message)
        return scenario, result


class SimulationScenarioMatrix(BaseModel):
    schema_version: str
    description: str
    cases: list[SimulationScenarioMatrixCase] = Field(default_factory=list)

    def __iter__(self) -> Iterator[SimulationScenarioMatrixCase]:  # type: ignore[override]
        return iter(self.cases)

    def by_id(self, case_id: str) -> SimulationScenarioMatrixCase:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise KeyError(case_id)


def load_simulation_scenario_matrix(path: Path) -> SimulationScenarioMatrix:
    data = read_json_file(path)
    if not isinstance(data, dict):
        raise ValueError(f"simulation scenario matrix JSON must be an object: {path}")
    matrix = SimulationScenarioMatrix.model_validate(data)
    for case in matrix.cases:
        if case.expected_result not in SUPPORTED_EXPECTED_RESULTS:
            raise ValueError(
                f"simulation scenario matrix case {case.case_id} has unsupported expected_result: "
                f"{case.expected_result}"
            )
        if case.expected_result == INVALID_INPUT and not case.expected_error_contains:
            raise ValueError(
                f"simulation scenario matrix case {case.case_id} must document expected_error_contains"
            )
    return matrix
