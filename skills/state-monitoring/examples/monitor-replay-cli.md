# monitor-replay CLI 示例

使用 entry point：

```bash
drone-ops monitor-replay --telemetry data/sample_logs/example_telemetry.csv --asset data/sample_assets/uav_001.json --rules data/sample_rules/monitoring_rules.yaml --out data/sample_reports/
```

未安装 entry point 时：

```bash
python -m apps.cli.main monitor-replay --telemetry data/sample_logs/example_telemetry.csv --asset data/sample_assets/uav_001.json --rules data/sample_rules/monitoring_rules.yaml --out data/sample_reports/
```

输出文件：

- `data/sample_reports/monitoring_summary.json`
- `data/sample_reports/monitoring_events.json`
- `data/sample_reports/audit/state-monitoring-*.json`

该命令只读取本地样例 telemetry，不连接真实无人机，也不执行任何真实动作。
