from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from apps.cli import main as cli


DEFAULT_OUTPUT_DIR = Path("demo_outputs")
DEMO_MARKER = ".drone-ops-demo-output"
DEMO_README_HEADER = "# 无人机运维 Agent 示例成果包"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def generate_demo_outputs(out_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    out_dir = validate_demo_output_dir(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / DEMO_MARKER).write_text("managed demo output directory\n", encoding="utf-8")

    reports_dir = out_dir / "reports"
    fleet_dir = out_dir / "fleet"
    dashboard_dir = out_dir / "dashboard"
    evals_dir = out_dir / "evals"
    platform_dir = out_dir / "platform"
    rules_dir = out_dir / "rules"
    adapters_dir = out_dir / "adapters"
    handoff_dir = out_dir / "handoff"
    preflight_dir = out_dir / "preflight"
    monitoring_dir = out_dir / "monitoring"

    for directory in (
        reports_dir,
        fleet_dir,
        dashboard_dir,
        evals_dir,
        platform_dir,
        rules_dir,
        adapters_dir,
        handoff_dir,
        preflight_dir,
        monitoring_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    cli._run_analyze_log(
        Path("data/sample_logs/example_flight.csv"),
        Path("data/sample_assets/uav_001.json"),
        reports_dir,
        "auto",
    )
    cli._run_diagnose(reports_dir / "flight_summary.json", Path("data/sample_assets/uav_001.json"), reports_dir)
    cli._run_validate_simulation(
        Path("data/sample_simulation/example_scenario.json"),
        Path("data/sample_simulation/example_simulation_result.json"),
        reports_dir,
    )
    cli._run_generate_work_orders(
        reports_dir / "maintenance_recommendations.json",
        Path("data/sample_assets/uav_001.json"),
        reports_dir,
    )
    cli._run_validate_work_orders(reports_dir / "work_order_drafts.json", reports_dir)
    cli._run_generate_report(
        reports_dir / "flight_summary.json",
        reports_dir / "diagnosis.json",
        reports_dir / "maintenance_recommendations.json",
        reports_dir / "ops_report.md",
        Path("data/sample_assets/uav_001.json"),
        reports_dir / "ops_report.pdf",
        reports_dir / "anomalies.json",
        reports_dir / "simulation_run.json",
        reports_dir / "work_order_drafts.json",
        reports_dir / "work_order_validation.json",
    )
    cli.validate_report_outputs(cli.ReportValidationPaths.from_report_dir(reports_dir), write_index=True)

    cli._run_preflight_check(
        Path("data/sample_assets/uav_001.json"),
        Path("data/sample_assets/battery_001.json"),
        Path("data/sample_missions/example_mission.json"),
        Path("data/sample_missions/preflight_observations_ok.json"),
        Path("data/sample_rules/preflight_rules.yaml"),
        preflight_dir,
    )
    cli._run_monitor_replay(
        Path("data/sample_logs/example_telemetry.csv"),
        Path("data/sample_assets/uav_001.json"),
        Path("data/sample_rules/monitoring_rules.yaml"),
        monitoring_dir,
    )
    cli._run_fleet_summary(Path("data/sample_fleet/fleet_manifest.json"), fleet_dir, fleet_dir / "fleet_health_report.md")
    cli._run_dashboard_bundle(
        reports_dir,
        dashboard_dir / "dashboard_bundle.json",
        fleet_dir / "fleet_health_summary.json",
        fleet_dir / "fleet_health_report.md",
    )
    cli._run_evals([Path("data/sample_evals/diagnosis_report_eval_case.json")], evals_dir)
    cli._run_validate_rule_pack(Path("data/sample_rule_packs/offline_default_rules.json"), rules_dir / "rule_pack_validation.json")
    cli._run_validate_datasets(Path("data/sample_datasets/registry.json"), platform_dir / "dataset_validation.json")
    cli._run_validate_adapters(Path("data/sample_adapters/offline_adapter_registry.json"), adapters_dir / "adapter_validation.json")
    cli._run_validate_approvals(Path("data/sample_approvals/approval_packet.json"), adapters_dir / "approval_validation.json")
    cli._run_validate_handoff_package(
        Path("data/sample_handoff/organization_handoff_package.json"),
        handoff_dir / "handoff_validation.json",
    )
    cli._run_validate_platform_index(
        Path("data/sample_platform/platform_readiness_index.json"),
        platform_dir / "platform_index_validation.json",
    )
    cli._run_validate_operations_platform(
        Path("data/sample_platform/operations_platform_baseline.json"),
        platform_dir / "operations_platform_validation.json",
    )

    _write_demo_readme(out_dir)
    return sorted(path.relative_to(out_dir) for path in out_dir.rglob("*") if path.is_file())


def validate_demo_output_dir(out_dir: Path) -> Path:
    target = Path(out_dir).expanduser().resolve()
    protected = {
        REPOSITORY_ROOT,
        Path.cwd().resolve(),
        Path.home().resolve(),
        Path(target.anchor).resolve(),
    }
    if target in protected or REPOSITORY_ROOT.is_relative_to(target):
        raise ValueError(f"拒绝将项目目录或其上级目录作为 demo 输出目录: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"demo 输出路径必须是目录: {target}")
    if target.exists() and any(target.iterdir()) and not _is_managed_demo_dir(target):
        raise ValueError(f"目标不是已生成的 demo 目录，拒绝清理: {target}")
    return target


def _is_managed_demo_dir(path: Path) -> bool:
    if (path / DEMO_MARKER).is_file():
        return True
    readme = path / "README.md"
    return readme.is_file() and readme.read_text(encoding="utf-8").startswith(DEMO_README_HEADER)


def _write_demo_readme(out_dir: Path) -> None:
    (out_dir / "README.md").write_text(
        """# 无人机运维 Agent 示例成果包

这个目录由 `python scripts/generate_demo_outputs.py --out demo_outputs` 生成，用于给自己和导师快速查看项目当前已经实现的离线运维能力。

## 推荐查看顺序

1. `reports/ops_report.md` 和 `reports/ops_report.pdf`：单次任务运维报告，包含异常、诊断、维护建议、仿真验证、工单草稿和人工复核清单。
2. `reports/evidence_index.json` 和 `reports/report_validation.json`：报告证据链索引和质量门禁结果。
3. `reports/simulation_run.json`：离线/mock 仿真验证结果和规则命中详情。
4. `reports/work_order_drafts.md` 和 `reports/work_order_validation.json`：本地工单草稿和工单质量门禁。
5. `fleet/fleet_health_report.md`：机队健康分析摘要。
6. `dashboard/dashboard_bundle.json`：本地只读 dashboard 数据包。
7. `platform/platform_index_validation.json` 和 `platform/operations_platform_validation.json`：平台 readiness index 与 v2.0 operations platform baseline 验证结果。

## 安全边界

所有内容均为 offline-only、advisory-only、human-review-required。该流程不连接真实无人机，不执行 MAVLink command，不启动 PX4 / ArduPilot / Gazebo / SITL，不接入真实维修系统或真实 fleet platform，也不会自动派单。
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local offline demo outputs for drone-ops-agent.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Demo output directory.")
    args = parser.parse_args()
    generated = generate_demo_outputs(args.out)
    print(f"Generated {len(generated)} demo files under {args.out}")


if __name__ == "__main__":
    main()
