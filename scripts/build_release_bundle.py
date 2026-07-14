from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
import zipfile
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INCLUDED_ROOTS = (".github", "agents", "apps", "constraints", "data", "docs", "evals", "packages", "scripts", "skills", "tests")
INCLUDED_TOP_LEVEL = (".gitignore", "README.md", "pyproject.toml")
EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", "build", "cache", "demo_outputs", "dist"}
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _project_version(source_root: Path) -> str:
    project = tomllib.loads((source_root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    return str(project["version"])


def _payload_files(source_root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(source_root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    files: list[Path] = []
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8"))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"invalid tracked path: {relative.as_posix()}")
        included = relative.as_posix() in INCLUDED_TOP_LEVEL or relative.parts[0] in INCLUDED_ROOTS
        if not included or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        path = source_root / relative
        if path.is_symlink():
            raise ValueError(f"release bundle refuses symbolic links: {relative.as_posix()}")
        if not path.is_file():
            raise ValueError(f"tracked release file is missing: {relative.as_posix()}")
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(source_root).as_posix())


def _zip_info(archive_path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(archive_path, FIXED_ZIP_TIMESTAMP)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (0o100644 & 0xFFFF) << 16
    return info


def build_release_bundle(source_root: Path, out_dir: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    out_dir = out_dir.resolve()
    version = _project_version(source_root)
    bundle_name = f"drone-ops-agent-{version}"
    zip_path = out_dir / f"{bundle_name}.zip"
    checksum_path = out_dir / f"{bundle_name}.zip.sha256"
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[tuple[str, bytes]] = []
    for path in _payload_files(source_root):
        relative = path.relative_to(source_root).as_posix()
        entries.append((relative, path.read_bytes()))

    file_manifest = [
        {"path": relative, "sha256": _sha256(data), "size": len(data)}
        for relative, data in entries
    ]
    manifest = {
        "file_count": len(file_manifest),
        "files": file_manifest,
        "project": "drone-ops-agent",
        "schema_version": "1.0.0",
        "version": version,
    }
    manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sums_data = "".join(f"{item['sha256']}  {item['path']}\n" for item in file_manifest).encode("utf-8")

    with zipfile.ZipFile(zip_path, "w") as archive:
        for relative, data in entries:
            archive.writestr(_zip_info(f"{bundle_name}/{relative}"), data)
        archive.writestr(_zip_info(f"{bundle_name}/distribution_manifest.json"), manifest_data)
        archive.writestr(_zip_info(f"{bundle_name}/SHA256SUMS"), sums_data)

    bundle_sha256 = _sha256(zip_path.read_bytes())
    checksum_path.write_text(f"{bundle_sha256}  {zip_path.name}\n", encoding="ascii")
    return {
        "bundle": zip_path,
        "bundle_sha256": bundle_sha256,
        "checksum": checksum_path,
        "file_count": len(file_manifest),
        "version": version,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic drone-ops-agent source release bundle.")
    parser.add_argument("--source", type=Path, default=REPOSITORY_ROOT, help="Repository source directory.")
    parser.add_argument("--out", type=Path, default=Path("dist/release"), help="Bundle output directory.")
    args = parser.parse_args()
    result = build_release_bundle(args.source, args.out)
    print(json.dumps({key: str(value) for key, value in result.items()}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
