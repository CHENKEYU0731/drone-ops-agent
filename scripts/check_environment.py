from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _dependency_status(requirement: str) -> dict[str, str | bool | None]:
    parsed = Requirement(requirement)
    name = parsed.name
    try:
        installed_version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        installed_version = None
    satisfies = installed_version is not None and parsed.specifier.contains(installed_version, prereleases=True)
    return {
        "installed": installed_version is not None,
        "installed_version": installed_version,
        "name": name,
        "requirement": requirement,
        "satisfies_requirement": satisfies,
    }


def check_environment(repository_root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    project = tomllib.loads((repository_root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    core = [_dependency_status(item) for item in project.get("dependencies", [])]
    optional = {
        group: [_dependency_status(item) for item in requirements]
        for group, requirements in sorted(project.get("optional-dependencies", {}).items())
    }
    python_supported = sys.version_info >= (3, 11)
    core_ready = all(item["satisfies_requirement"] for item in core)
    return {
        "checks": {
            "core_dependencies_installed": core_ready,
            "python_supported": python_supported,
        },
        "core_dependencies": core,
        "optional_dependencies": optional,
        "platform": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "system": platform.system(),
        },
        "project": {
            "name": project["name"],
            "version": project["version"],
        },
        "safety_boundary": {
            "advisory_only": True,
            "human_review_required": True,
            "offline_runtime": True,
        },
        "schema_version": "1.0.0",
        "status": "PASS" if python_supported and core_ready else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the local drone-ops-agent distribution environment.")
    parser.add_argument("--out", type=Path, help="Optional JSON output path.")
    parser.add_argument("--require-pass", action="store_true", help="Exit with status 1 unless all core checks pass.")
    args = parser.parse_args()
    payload = json.dumps(check_environment(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if args.require_pass and json.loads(payload)["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
