from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tomllib
import zipfile
from pathlib import Path
from typing import Any

if __package__:
    from .generate_demo_outputs import generate_demo_outputs
else:
    from generate_demo_outputs import generate_demo_outputs


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path("portfolio_showcase")
PORTFOLIO_MARKER = ".drone-ops-portfolio-output"
PORTFOLIO_MARKER_CONTENT = "managed portfolio output directory\n"
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".json", ".md", ".stderr", ".txt"}
FORBIDDEN_BINARY_SUFFIXES = {".bin", ".ulg"}
PORTFOLIO_DOCS = (
    Path("docs/portfolio/项目总览.md"),
    Path("docs/portfolio/project_overview_en.md"),
    Path("docs/portfolio/capability_matrix.md"),
    Path("docs/portfolio/demo_script.md"),
)
SHOWCASE_ASSETS = (
    Path("docs/assets/showcase/dashboard_overview.png"),
    Path("docs/assets/showcase/ops_report_preview.png"),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_portfolio_output_dir(out_dir: Path) -> Path:
    target = Path(out_dir).expanduser().resolve()
    protected = {
        REPOSITORY_ROOT,
        Path.cwd().resolve(),
        Path.home().resolve(),
        Path(target.anchor).resolve(),
    }
    if target in protected or REPOSITORY_ROOT.is_relative_to(target):
        raise ValueError(f"拒绝将项目目录或其上级目录作为 portfolio 输出目录: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"portfolio 输出路径必须是目录: {target}")
    if target.exists() and any(target.iterdir()):
        marker = target / PORTFOLIO_MARKER
        managed = (
            marker.is_file()
            and not marker.is_symlink()
            and marker.read_text(encoding="utf-8") == PORTFOLIO_MARKER_CONTENT
        )
        if not managed:
            raise ValueError(f"目标不是已生成的 portfolio 目录，拒绝清理: {target}")
    return target


def _write_portfolio_readme(out_dir: Path) -> None:
    (out_dir / "README.md").write_text(
        """# drone-ops-agent 最终作品展示包

这个目录用于向导师、招聘方和项目维护者展示当前已完成的离线无人机运维决策支持能力。

建议先阅读 `guides/项目总览.md` 和 `guides/demo_script.md`，再查看 `demo_outputs/reports/ops_report.pdf`、`demo_outputs/case_studies/case_study_report.md`、`demo_outputs/fleet/fleet_health_report.md` 与 `demo_outputs/dashboard/dashboard_bundle.json`。

所有演示输入均为仓库内 sample / mock / sanitized fixture。该成果包不包含外部 ULog 缓存、真实敏感飞行日志或凭据，不代表真实飞行授权、维修授权或模型在真实世界的准确率。

系统保持 offline-only、advisory-only 和 human-review-required；不连接真实无人机，不执行 MAVLink command，不启动 PX4、ArduPilot、Gazebo 或 SITL。
""",
        encoding="utf-8",
    )


def _copy_portfolio_materials(out_dir: Path) -> None:
    guides_dir = out_dir / "guides"
    assets_dir = out_dir / "assets"
    guides_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    for relative in PORTFOLIO_DOCS:
        shutil.copyfile(REPOSITORY_ROOT / relative, guides_dir / relative.name)
    for relative in SHOWCASE_ASSETS:
        shutil.copyfile(REPOSITORY_ROOT / relative, assets_dir / relative.name)


def _artifact_manifest(out_dir: Path) -> list[dict[str, Any]]:
    repository_paths = {str(REPOSITORY_ROOT), REPOSITORY_ROOT.as_posix()}
    artifacts: list[dict[str, Any]] = []
    for path in sorted(out_dir.rglob("*"), key=lambda item: item.relative_to(out_dir).as_posix()):
        if not path.is_file() or path.name == "portfolio_manifest.json":
            continue
        relative = path.relative_to(out_dir).as_posix()
        if path.suffix.lower() in FORBIDDEN_BINARY_SUFFIXES:
            raise ValueError(f"portfolio bundle refuses raw flight-log binaries: {relative}")
        data = path.read_bytes()
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = data.decode("utf-8", errors="replace")
            if any(repository_path in text for repository_path in repository_paths):
                raise ValueError(f"portfolio artifact leaks repository path: {relative}")
        artifacts.append({"path": relative, "sha256": _sha256(data), "size": len(data)})
    return artifacts


def _zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, FIXED_ZIP_TIMESTAMP)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (0o100644 & 0xFFFF) << 16
    return info


def _project_version() -> str:
    return str(tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])


def _write_archive(out_dir: Path, archive_path: Path, version: str) -> str:
    _reject_unsafe_output_file(archive_path)
    root_name = f"drone-ops-agent-v{version}-showcase"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path in sorted(out_dir.rglob("*"), key=lambda item: item.relative_to(out_dir).as_posix()):
            if path.is_file():
                relative = path.relative_to(out_dir).as_posix()
                archive.writestr(_zip_info(f"{root_name}/{relative}"), path.read_bytes())
    return _sha256(archive_path.read_bytes())


def build_portfolio_showcase(out_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    out_dir = validate_portfolio_output_dir(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / PORTFOLIO_MARKER).write_text(PORTFOLIO_MARKER_CONTENT, encoding="utf-8")

    generate_demo_outputs(out_dir / "demo_outputs")
    _copy_portfolio_materials(out_dir)
    _write_portfolio_readme(out_dir)
    artifacts = _artifact_manifest(out_dir)
    version = _project_version()
    manifest = {
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "data_policy": {
            "external_binary_logs_included": False,
            "real_world_accuracy_claimed": False,
            "sample_mock_sanitized_only": True,
        },
        "project": "drone-ops-agent",
        "safety_boundary": {
            "advisory_only": True,
            "human_review_required": True,
            "offline_only": True,
        },
        "schema_version": "1.0.0",
        "version": version,
    }
    (out_dir / "portfolio_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    archive_path = out_dir.parent / f"{out_dir.name}.zip"
    archive_sha256 = _write_archive(out_dir, archive_path, version)
    checksum_path = archive_path.parent / f"{archive_path.name}.sha256"
    _reject_unsafe_output_file(checksum_path)
    checksum_path.write_text(f"{archive_sha256}  {archive_path.name}\n", encoding="ascii")
    return {
        "archive": archive_path,
        "archive_sha256": archive_sha256,
        "artifact_count": len(artifacts),
        "checksum": checksum_path,
        "output_dir": out_dir,
    }


def _reject_unsafe_output_file(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing symbolic-link output: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"output path must be a regular file: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the final sanitized drone-ops-agent portfolio showcase.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Managed showcase output directory.")
    args = parser.parse_args()
    result = build_portfolio_showcase(args.out)
    print(json.dumps({key: str(value) for key, value in result.items()}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
