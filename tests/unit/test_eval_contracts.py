from pathlib import Path

from packages.drone_schemas import (
    EvalCase,
    EvalExpectedOutput,
    EvalMetric,
    EvalResult,
    EvalStatus,
    load_model,
)


def test_eval_contract_supports_diagnosis_report_quality_gate() -> None:
    metric = EvalMetric(
        metric_id="evidence_completeness",
        name="Evidence completeness",
        description="Diagnosis, maintenance, and report outputs cite expected evidence refs.",
        weight=0.25,
        pass_threshold=1.0,
        review_threshold=0.75,
        required_evidence_refs=["BATTERY_LOW_SOC@anomalies.json#ANOM-001"],
    )
    expected = EvalExpectedOutput(
        expected_status=EvalStatus.PASS,
        required_diagnosis_ids=["FAULT-BATTERY-001"],
        required_recommendation_ids=["MAINT-BATTERY-001"],
        required_report_sections=["## Diagnosis", "## Maintenance Recommendations", "## Evidence"],
        required_evidence_refs=["BATTERY_LOW_SOC@anomalies.json#ANOM-001"],
    )
    case = EvalCase(
        case_id="diagnosis-report-golden",
        title="Diagnosis and report golden case",
        input_refs={
            "diagnosis": "diagnosis.json",
            "maintenance": "maintenance_recommendations.json",
            "report": "ops_report.md",
        },
        metrics=[metric],
        expected_output=expected,
        safety_boundary={
            "offline_only": True,
            "advisory_only": True,
            "no_external_model_call": True,
        },
    )

    result = EvalResult(
        case_id=case.case_id,
        status=EvalStatus.PASS,
        score=1.0,
        metric_results=[
            {
                "metric_id": "evidence_completeness",
                "status": "PASS",
                "score": 1.0,
                "evidence_refs": ["BATTERY_LOW_SOC@anomalies.json#ANOM-001"],
                "message": "All expected evidence refs were present.",
            }
        ],
        findings=[],
        output_refs=["eval_results.json"],
    )

    assert case.human_review_required is True
    assert case.metrics[0].weight == 0.25
    assert case.expected_output.expected_status == EvalStatus.PASS
    assert result.human_review_required is True
    assert result.status == EvalStatus.PASS


def test_sample_eval_case_fixture_loads_with_stable_metric_order() -> None:
    case = load_model(Path("data/sample_evals/diagnosis_report_eval_case.json"), EvalCase)

    assert case.case_id == "diagnosis-report-golden"
    assert [metric.metric_id for metric in case.metrics] == sorted(metric.metric_id for metric in case.metrics)
    assert case.expected_output.expected_status == EvalStatus.PASS
    assert case.safety_boundary["offline_only"] is True
