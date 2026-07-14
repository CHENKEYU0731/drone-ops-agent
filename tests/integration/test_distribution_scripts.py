from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


def test_distribution_scripts_emit_valid_artifacts(tmp_path: Path) -> None:
    environment_path = tmp_path / "environment.json"
    subprocess.run(
        [sys.executable, "scripts/check_environment.py", "--out", str(environment_path)],
        check=True,
    )
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    assert environment["status"] in {"PASS", "FAIL"}
    assert all("satisfies_requirement" in item for item in environment["core_dependencies"])

    completed = subprocess.run(
        [sys.executable, "scripts/build_release_bundle.py", "--out", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    output = json.loads(completed.stdout)
    bundle = Path(output["bundle"])
    assert bundle.is_file()
    assert Path(output["checksum"]).is_file()
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
