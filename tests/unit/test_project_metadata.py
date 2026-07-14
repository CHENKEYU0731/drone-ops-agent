from pathlib import Path

from apps.cli.main import app


def test_project_metadata_matches_latest_major_release() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'version = "2.5.0"' in pyproject
    assert 'description = "Offline drone operations decision support platform"' in pyproject
    assert "MVP" not in app.info.help
    assert "决策支持平台" in Path("README.md").read_text(encoding="utf-8").splitlines()[2]


def test_roadmaps_record_v2_release_as_completed() -> None:
    roadmap = Path("docs/roadmap.md").read_text(encoding="utf-8")
    detailed = Path("docs/planning/v0.8-to-v2.0-roadmap.md").read_text(encoding="utf-8")

    assert "项目当前版本为 `v2.5.0" in roadmap
    assert "项目当前已发布到 `v2.0.0" in detailed
    assert "| `v2.0.0` | Operations Platform Baseline" in detailed
    assert "| 已完成 |" in detailed
