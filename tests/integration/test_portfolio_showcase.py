from __future__ import annotations

import json
import tomllib
import zipfile
from pathlib import Path

import pytest

from scripts.build_portfolio_showcase import build_portfolio_showcase, validate_portfolio_output_dir


def test_portfolio_showcase_contains_sanitized_review_materials(tmp_path: Path) -> None:
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    result = build_portfolio_showcase(tmp_path / "portfolio")
    out_dir = result["output_dir"]

    expected = {
        "README.md",
        "portfolio_manifest.json",
        "guides/项目总览.md",
        "guides/project_overview_en.md",
        "guides/capability_matrix.md",
        "guides/demo_script.md",
        "guides/resume_and_interview_guide.md",
        "assets/dashboard_overview.png",
        "assets/ops_report_preview.png",
        "demo_outputs/reports/ops_report.pdf",
        "demo_outputs/reports/evidence_index.json",
        "demo_outputs/case_studies/case_study_report.md",
    }
    actual = {path.relative_to(out_dir).as_posix() for path in out_dir.rglob("*") if path.is_file()}
    assert expected.issubset(actual)
    assert not any(path.endswith((".ulg", ".bin")) for path in actual)

    manifest = json.loads((out_dir / "portfolio_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == version
    assert manifest["data_policy"] == {
        "external_binary_logs_included": False,
        "real_world_accuracy_claimed": False,
        "sample_mock_sanitized_only": True,
    }
    assert manifest["safety_boundary"]["human_review_required"] is True
    assert result["archive"].is_file()
    assert result["archive"].name == "portfolio.zip"
    assert result["checksum"].name == "portfolio.zip.sha256"
    assert result["checksum"].read_text(encoding="ascii").startswith(result["archive_sha256"])
    with zipfile.ZipFile(result["archive"]) as archive:
        assert archive.testzip() is None
        assert all(name.startswith(f"drone-ops-agent-v{version}-showcase/") for name in archive.namelist())


def test_portfolio_output_validation_rejects_unmanaged_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "existing"
    out_dir.mkdir()
    (out_dir / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="不是已生成"):
        validate_portfolio_output_dir(out_dir)

    assert (out_dir / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_portfolio_output_validation_rejects_spoofed_marker(tmp_path: Path) -> None:
    out_dir = tmp_path / "spoofed"
    out_dir.mkdir()
    (out_dir / ".drone-ops-portfolio-output").write_text("spoofed\n", encoding="utf-8")
    (out_dir / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="不是已生成"):
        validate_portfolio_output_dir(out_dir)

    assert (out_dir / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_portfolio_output_validation_rejects_symlink_marker(tmp_path: Path) -> None:
    out_dir = tmp_path / "symlink-marker"
    out_dir.mkdir()
    marker_target = tmp_path / "marker-target"
    marker_target.write_text("managed portfolio output directory\n", encoding="utf-8")
    try:
        (out_dir / ".drone-ops-portfolio-output").symlink_to(marker_target)
    except OSError as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")
    (out_dir / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="不是已生成"):
        validate_portfolio_output_dir(out_dir)

    assert (out_dir / "keep.txt").read_text(encoding="utf-8") == "keep"
