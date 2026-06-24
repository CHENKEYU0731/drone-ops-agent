# preflight-check 测试用例

- `preflight_observations_ok.json` + `battery_001.json`：期望 `GO`。
- `preflight_observations_warning.json` + `battery_degraded.json`：期望 `REVIEW_REQUIRED`。
- `preflight_observations_blocking.json` + 低 SOC 或 grounded 资产：期望 `NO_GO`。
- 每个 warning 和 blocking item 必须包含 evidence refs。
- 每次 CLI 运行必须生成 audit JSON。
