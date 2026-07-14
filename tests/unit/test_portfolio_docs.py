from pathlib import Path


def test_portfolio_documents_cover_capabilities_and_evidence_boundaries() -> None:
    chinese = Path("docs/portfolio/项目总览.md").read_text(encoding="utf-8")
    english = Path("docs/portfolio/project_overview_en.md").read_text(encoding="utf-8")
    matrix = Path("docs/portfolio/capability_matrix.md").read_text(encoding="utf-8")
    demo = Path("docs/portfolio/demo_script.md").read_text(encoding="utf-8")
    interview = Path("docs/portfolio/resume_and_interview_guide.md").read_text(encoding="utf-8")

    for text in (chinese, english, matrix, demo, interview):
        assert "offline-only" in text
        assert "MAVLink" in text

    assert "real_world_flight_verified=false" in chinese
    assert "real_world_flight_verified=false" in english
    assert "14" in matrix and "15" in matrix
    assert "第 4–5 分钟" in demo
    assert "English Resume Version" in interview
    assert "不等于真实飞行故障检测准确率" in interview
