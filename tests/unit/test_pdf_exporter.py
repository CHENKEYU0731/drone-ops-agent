import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader

from packages.report_templates import pdf_exporter
from packages.report_templates.pdf_exporter import PDF_FONT_ENV_VAR, export_markdown_to_pdf, resolve_pdf_font_path


def test_export_markdown_to_pdf_writes_valid_pdf(tmp_path: Path) -> None:
    markdown = tmp_path / "ops_report.md"
    pdf = tmp_path / "ops_report.pdf"
    markdown.write_text(
        """
# 无人机运维报告

## 1. 执行摘要

- 无人机：UAV-001
- 本报告仅用于离线运维分析。

## 11. 证据引用附录

- MON_LOW_BATTERY_SOC@data/sample_logs/example_telemetry.csv:4
""".strip(),
        encoding="utf-8",
    )

    export_markdown_to_pdf(markdown, pdf)

    assert pdf.exists()
    assert pdf.stat().st_size > 100
    assert pdf.read_bytes().startswith(b"%PDF")
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf)).pages)
    assert "无人机运维报告" in text
    assert "MON_LOW_BATTERY_SOC" in text


def test_resolve_pdf_font_path_uses_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    font = tmp_path / "custom-font.ttf"
    font.write_bytes(b"font")
    monkeypatch.setenv(PDF_FONT_ENV_VAR, str(font))
    monkeypatch.setattr(pdf_exporter, "_is_reportlab_font", lambda path: True)

    assert resolve_pdf_font_path() == font


def test_resolve_pdf_font_path_reports_missing_font(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PDF_FONT_ENV_VAR, raising=False)
    monkeypatch.setattr(pdf_exporter, "CJK_FONT_CANDIDATES", [])

    with pytest.raises(RuntimeError, match=PDF_FONT_ENV_VAR):
        resolve_pdf_font_path()


def test_resolve_pdf_font_path_skips_unusable_font_candidate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    unusable = tmp_path / "unusable.ttf"
    usable = tmp_path / "usable.ttf"
    unusable.write_bytes(b"not a font")
    usable.write_bytes(b"pretend font")
    monkeypatch.delenv(PDF_FONT_ENV_VAR, raising=False)
    monkeypatch.setattr(pdf_exporter, "CJK_FONT_CANDIDATES", [unusable, usable])
    monkeypatch.setattr(pdf_exporter, "_is_reportlab_font", lambda path: path == usable)

    assert resolve_pdf_font_path() == usable


def test_resolve_pdf_font_path_rejects_unusable_env_font(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    font = tmp_path / "custom-font.ttf"
    font.write_bytes(b"not a font")
    monkeypatch.setenv(PDF_FONT_ENV_VAR, str(font))
    monkeypatch.setattr(pdf_exporter, "_is_reportlab_font", lambda path: False)

    with pytest.raises(RuntimeError, match="cannot embed"):
        resolve_pdf_font_path()


def test_export_markdown_to_pdf_uses_env_font_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    font_path = _available_cjk_font()
    monkeypatch.setenv(PDF_FONT_ENV_VAR, str(font_path))
    markdown = tmp_path / "ops_report.md"
    pdf = tmp_path / "ops_report.pdf"
    markdown.write_text("# 无人机运维报告\n\n- 证据：LOW_BATTERY_SOC\n", encoding="utf-8")

    export_markdown_to_pdf(markdown, pdf)

    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF")


def test_export_markdown_to_pdf_renders_with_poppler_when_available(tmp_path: Path) -> None:
    if shutil.which("pdftoppm") is None:
        pytest.skip("pdftoppm is not installed")
    _available_cjk_font()
    markdown = tmp_path / "ops_report.md"
    pdf = tmp_path / "ops_report.pdf"
    png_prefix = tmp_path / "ops_report_page1"
    markdown.write_text("# 无人机运维报告\n\n## 执行摘要\n\n- 证据：LOW_BATTERY_SOC\n", encoding="utf-8")
    export_markdown_to_pdf(markdown, pdf)

    result = subprocess.run(
        ["pdftoppm", "-png", "-f", "1", "-singlefile", str(pdf), str(png_prefix)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Missing language pack" not in result.stderr
    assert "Unknown font tag" not in result.stderr
    assert (tmp_path / "ops_report_page1.png").stat().st_size > 0


def test_export_markdown_to_pdf_rejects_missing_markdown(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError, match="missing.md"):
        export_markdown_to_pdf(missing, tmp_path / "out.pdf")


def test_export_markdown_to_pdf_rejects_empty_markdown(tmp_path: Path) -> None:
    markdown = tmp_path / "empty.md"
    markdown.write_text("  \n", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        export_markdown_to_pdf(markdown, tmp_path / "out.pdf")


def test_export_markdown_to_pdf_reports_invalid_output_path(tmp_path: Path) -> None:
    markdown = tmp_path / "ops_report.md"
    markdown.write_text("# Report\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not write PDF"):
        export_markdown_to_pdf(markdown, tmp_path)


def _available_cjk_font() -> Path:
    try:
        return resolve_pdf_font_path()
    except RuntimeError as exc:
        pytest.skip(str(exc))
