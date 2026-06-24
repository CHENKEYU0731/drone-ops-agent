from __future__ import annotations

import os
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


PDF_FONT_ENV_VAR = "DRONE_OPS_PDF_FONT_PATH"
PDF_FONT_NAME = "DroneOpsCJK"
CJK_FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    Path("/usr/share/fonts/truetype/arphic/uming.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
]


def export_markdown_to_pdf(markdown_path: Path, output_path: Path) -> None:
    try:
        markdown = markdown_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Markdown input does not exist: {markdown_path}") from exc
    if not markdown.strip():
        raise ValueError(f"Markdown input is empty: {markdown_path}")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=markdown_path.stem,
        )
        doc.build(_markdown_story(markdown))
    except OSError as exc:
        raise ValueError(f"Could not write PDF output: {output_path}: {exc}") from exc


def _markdown_story(markdown: str) -> list:
    styles = _styles()
    story: list = []
    in_code = False
    code_lines: list[str] = []

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["Code"]))
                story.append(Spacer(1, 6))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            story.append(Spacer(1, 5))
            continue
        paragraph = _line_to_flowable(line, styles)
        story.append(paragraph)
        story.append(Spacer(1, 4))

    if code_lines:
        story.append(Preformatted("\n".join(code_lines), styles["Code"]))
    return story


def _line_to_flowable(line: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    stripped = line.strip()
    if stripped.startswith("# "):
        return Paragraph(_inline(stripped[2:]), styles["Title"])
    if stripped.startswith("## "):
        return Paragraph(_inline(stripped[3:]), styles["Heading1"])
    if stripped.startswith("### "):
        return Paragraph(_inline(stripped[4:]), styles["Heading2"])
    if stripped.startswith("- "):
        return Paragraph(f"- {_inline(stripped[2:])}", styles["Bullet"])
    if stripped.startswith("* "):
        return Paragraph(f"- {_inline(stripped[2:])}", styles["Bullet"])
    return Paragraph(_inline(stripped), styles["Body"])


def _inline(text: str) -> str:
    escaped = escape(text)
    parts = escaped.split("`")
    for index in range(1, len(parts), 2):
        parts[index] = f"<font name='{PDF_FONT_NAME}'>{parts[index]}</font>"
    return "".join(parts)


def _styles() -> dict[str, ParagraphStyle]:
    font_name = _font_name()
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "DroneOpsTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=18,
            leading=24,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=8,
        ),
        "Heading1": ParagraphStyle(
            "DroneOpsHeading1",
            parent=base["Heading1"],
            fontName=font_name,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Heading2": ParagraphStyle(
            "DroneOpsHeading2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#374151"),
        ),
        "Body": ParagraphStyle(
            "DroneOpsBody",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#111827"),
        ),
        "Bullet": ParagraphStyle(
            "DroneOpsBullet",
            parent=base["BodyText"],
            fontName=font_name,
            leftIndent=12,
            firstLineIndent=-8,
            fontSize=9.5,
            leading=14,
        ),
        "Code": ParagraphStyle(
            "DroneOpsCode",
            parent=base["Code"],
            fontName=font_name,
            fontSize=8,
            leading=10,
            backColor=colors.HexColor("#F3F4F6"),
        ),
    }


def _font_name() -> str:
    font_path = resolve_pdf_font_path()
    if PDF_FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(font_path), subfontIndex=0))
        except TTFError as exc:
            raise RuntimeError(f"PDF font cannot be embedded by ReportLab: {font_path}: {exc}") from exc
    return PDF_FONT_NAME


def resolve_pdf_font_path() -> Path:
    env_font = os.getenv(PDF_FONT_ENV_VAR)
    if env_font:
        env_path = Path(env_font).expanduser()
        if not env_path.is_file():
            raise RuntimeError(f"{PDF_FONT_ENV_VAR} points to a missing PDF font: {env_path}")
        if _is_reportlab_font(env_path):
            return env_path
        raise RuntimeError(
            f"{PDF_FONT_ENV_VAR} points to a font ReportLab cannot embed: {env_path}. "
            "Use a CJK TrueType/OpenType font with TrueType outlines."
        )

    rejected: list[str] = []
    for candidate in CJK_FONT_CANDIDATES:
        if candidate.is_file() and _is_reportlab_font(candidate):
            return candidate
        if candidate.is_file():
            rejected.append(str(candidate))

    searched = "\n".join(f"- {path}" for path in CJK_FONT_CANDIDATES)
    rejected_text = "\n".join(f"- {path}" for path in rejected) or "- none"
    raise RuntimeError(
        "No embeddable CJK font was found for PDF export. "
        f"Install a CJK font or set {PDF_FONT_ENV_VAR}=/path/to/font.ttf.\n"
        f"Searched paths:\n{searched}\n"
        f"Rejected existing fonts that ReportLab cannot embed:\n{rejected_text}"
    )


def _is_reportlab_font(font_path: Path) -> bool:
    try:
        TTFont(f"{PDF_FONT_NAME}Probe", str(font_path), subfontIndex=0)
    except TTFError:
        return False
    return True
