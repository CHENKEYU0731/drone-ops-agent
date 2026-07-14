from pathlib import Path

import pytest

from packages.drone_schemas import read_json_file
from packages.drone_schemas.io import MAX_JSON_FILE_BYTES
from packages.log_parsers import parse_flight_log_details
from packages.log_parsers.parser import MAX_FLIGHT_LOG_BYTES
from packages.report_templates.pdf_exporter import MAX_MARKDOWN_FILE_BYTES, export_markdown_to_pdf


def _write_sparse_file(path: Path, size: int) -> None:
    with path.open("wb") as handle:
        handle.seek(size)
        handle.write(b"x")


def test_oversized_json_is_rejected_before_read(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    _write_sparse_file(path, MAX_JSON_FILE_BYTES)

    with pytest.raises(ValueError, match="超过大小限制"):
        read_json_file(path)


def test_non_finite_json_number_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "nan.json"
    path.write_text('{"value": NaN}', encoding="utf-8")

    with pytest.raises(ValueError, match="不允许常量 NaN"):
        read_json_file(path)


def test_oversized_flight_log_is_rejected_before_parser(tmp_path: Path) -> None:
    path = tmp_path / "large.ulg"
    _write_sparse_file(path, MAX_FLIGHT_LOG_BYTES)

    with pytest.raises(ValueError, match="超过大小限制"):
        parse_flight_log_details(path, requested_format="px4-ulog")


def test_oversized_markdown_is_rejected_before_pdf_render(tmp_path: Path) -> None:
    path = tmp_path / "large.md"
    _write_sparse_file(path, MAX_MARKDOWN_FILE_BYTES)

    with pytest.raises(ValueError, match="exceeds"):
        export_markdown_to_pdf(path, tmp_path / "out.pdf")
