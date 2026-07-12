from pathlib import Path


def test_demo_guide_documents_local_showcase_workflow() -> None:
    text = Path("docs/demo_guide.md").read_text(encoding="utf-8")

    assert "python scripts/generate_demo_outputs.py --out demo_outputs" in text
    assert "demo_outputs" in text
    assert "ops_report.pdf" in text
    assert "evidence_index.json" in text
    assert "simulation_run.json" in text
    assert "work_order_drafts.md" in text
    assert "fleet_health_report.md" in text
    assert "operations_platform_validation.json" in text
    assert "offline-only" in text
    assert "advisory-only" in text
    assert "不连接真实无人机" in text
