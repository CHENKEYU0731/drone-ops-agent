# preflight-check 示例

```bash
drone-ops preflight-check --asset data/sample_assets/uav_001.json --battery data/sample_assets/battery_001.json --mission data/sample_missions/example_mission.json --observations data/sample_missions/preflight_observations_ok.json --rules data/sample_rules/preflight_rules.yaml --out data/sample_reports/
```

输出：

- `data/sample_reports/preflight_check_result.json`
- `data/sample_reports/audit/preflight-check-<run_id>.json`

`GO` 只表示离线检查未发现 warning 或 blocking item，不代表自动授权真实飞行。
