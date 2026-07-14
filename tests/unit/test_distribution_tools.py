from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.build_release_bundle import build_release_bundle
from scripts.check_environment import check_environment


def test_environment_diagnostic_has_stable_structure() -> None:
    result = check_environment()

    assert result["schema_version"] == "1.0.0"
    assert result["project"] == {"name": "drone-ops-agent", "version": "2.4.0"}
    assert result["safety_boundary"] == {
        "advisory_only": True,
        "human_review_required": True,
        "offline_runtime": True,
    }
    assert [item["name"] for item in result["core_dependencies"]] == [
        "packaging",
        "pydantic",
        "reportlab",
        "starlette",
        "typer",
    ]


def test_release_bundle_is_deterministic_and_self_describing(tmp_path: Path) -> None:
    first = build_release_bundle(Path.cwd(), tmp_path / "first")
    second = build_release_bundle(Path.cwd(), tmp_path / "second")

    assert first["bundle_sha256"] == second["bundle_sha256"]
    assert first["file_count"] == second["file_count"]
    assert first["checksum"].read_text(encoding="ascii").endswith("  drone-ops-agent-2.4.0.zip\n")

    with zipfile.ZipFile(first["bundle"]) as archive:
        names = archive.namelist()
        assert names == sorted(names[:-2]) + names[-2:]
        assert "drone-ops-agent-2.4.0/distribution_manifest.json" in names
        assert "drone-ops-agent-2.4.0/SHA256SUMS" in names
        assert not any("open_source_logs/cache" in name for name in names)
        assert [name for name in names if "/data/sample_reports/" in name] == [
            "drone-ops-agent-2.4.0/data/sample_reports/.gitkeep"
        ]
        manifest = json.loads(archive.read("drone-ops-agent-2.4.0/distribution_manifest.json"))
        assert manifest["version"] == "2.4.0"
        assert manifest["file_count"] == first["file_count"]


def test_direct_dependency_constraints_are_exact() -> None:
    for path in sorted(Path("constraints").glob("*.txt")):
        requirements = [line for line in path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        assert requirements
        assert all("==" in requirement for requirement in requirements)
