from __future__ import annotations

import re
from pathlib import Path


RUNTIME_ROOTS = [Path("apps"), Path("packages")]

FORBIDDEN_RUNTIME_PATTERNS = {
    "mavlink connection": re.compile(r"\bmavutil\.mavlink_connection\b"),
    "mavlink command send": re.compile(r"\bcommand_long_send\b|\bMAV_CMD_\w+"),
    "parameter write": re.compile(r"\bparam_set_send\b|\bparameter_write\b"),
    "mode or mission send": re.compile(r"\bset_mode_send\b|\bmission_(item|count|write)_send\b"),
    "real simulator launch": re.compile(r"\b(px4|ardupilot|gazebo|sitl)\b.*\b(Popen|run|call)\b", re.IGNORECASE),
    "network client": re.compile(r"\brequests\.|\bhttpx\.|\burllib\.request\b|\bsocket\.socket\b"),
}

REQUIRED_BOUNDARY_TEXT = [
    "offline-only",
    "advisory-only",
    "MAVLink command",
    "PX4",
    "ArduPilot",
    "Gazebo",
    "SITL",
    "CMMS",
    "Jira",
    "飞书",
    "企业微信",
]


def _python_runtime_files() -> list[Path]:
    files: list[Path] = []
    for root in RUNTIME_ROOTS:
        files.extend(sorted(root.rglob("*.py")))
    return files


def test_runtime_code_has_no_real_control_or_network_paths() -> None:
    findings: list[str] = []
    for path in _python_runtime_files():
        text = path.read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN_RUNTIME_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path}: forbidden {label}")

    assert findings == []


def test_v1_safety_regression_gate_document_exists() -> None:
    path = Path("docs/v1.0.0_safety_regression_gate.md")
    assert path.exists()

    text = path.read_text(encoding="utf-8")
    for required in REQUIRED_BOUNDARY_TEXT:
        assert required in text


def test_v1_release_notes_record_safety_regression_gate() -> None:
    text = Path("docs/releases/v1.0.0-draft.md").read_text(encoding="utf-8")

    assert "Safety Regression Gate" in text
    assert "tests/unit/test_v1_safety_regression_gate.py" in text
