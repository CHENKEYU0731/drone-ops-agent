from pathlib import Path


def test_v2_5_2_separates_public_project_materials_from_local_notes() -> None:
    assert not Path("docs/portfolio/resume_and_interview_guide.md").exists()
    assert "local_notes/" in Path(".gitignore").read_text(encoding="utf-8")

    public_text = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "README.md",
            "docs/demo_guide.md",
            "docs/codex_workflows.md",
            "scripts/build_portfolio_showcase.py",
        )
    )
    assert "resume_and_interview_guide" not in public_text
    assert not any(term in public_text for term in ("简历", "面试", "求职"))

    readiness = Path("docs/v2.5.2_release_readiness.md").read_text(encoding="utf-8")
    release = Path("docs/releases/v2.5.2-draft.md").read_text(encoding="utf-8")
    for text in (readiness, release):
        assert "offline-only" in text
        assert "advisory-only" in text
        assert "human-review-required" in text
