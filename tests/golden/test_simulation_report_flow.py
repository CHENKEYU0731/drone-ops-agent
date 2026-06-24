from pathlib import Path


def test_simulation_skill_documents_report_integration_point() -> None:
    text = Path("skills/simulation-validation/SKILL.md").read_text(encoding="utf-8")

    assert "validate-simulation" in text
    assert "simulation_run.json" in text
    assert "ops_report.md" in text
