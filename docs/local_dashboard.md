# v1.2.0 本地只读 Dashboard

`v1.2.0 - Local Web Dashboard MVP` 的目标是把现有 CLI 输出整理成一个本地、只读、
可视化友好的入口。Dashboard 只能读取本地 sample / mock / sanitized artifact，不连接真实
无人机、真实 fleet platform、真实维修系统或外部仿真器。

## Dashboard Data Bundle Baseline

第一阶段新增 `dashboard_bundle.json`，用于给后续本地 backend 和 Web UI 提供稳定数据源。

生成命令：

```bash
python -m apps.cli.main dashboard-bundle \
  --report-dir data/sample_reports \
  --fleet-summary data/sample_reports/fleet_health_summary.json \
  --fleet-report data/sample_reports/fleet_health_report.md \
  --out /tmp/dashboard_bundle.json
```

当前 bundle 包含：

- `report`：本地报告目录、`ops_report.md`、`report_validation.json`
- `simulation`：`simulation_run.json`
- `work_orders`：工单草稿和工单验证输出路径
- `fleet_health`：机队健康摘要和 Markdown 报告路径
- `audit`：本地 audit 目录路径
- `evidence`：`evidence_index.json`

普通 CLI 保留调用方传入的本地路径；`generate_demo_outputs.py` 生成的作品展示成果包会将这些引用写成相对于 `demo_outputs/` 的路径，便于整体移动和分享。

## 安全边界

Dashboard bundle 只保存本地 artifact reference，不读取实时遥测，不调用外部 API，不启动服务，
也不执行任何飞控或维护动作。

## Local Read-only Backend Baseline

第二阶段新增一个轻量本地 ASGI backend factory：

- `packages.dashboard.create_dashboard_app(bundle_path=...)`
- `GET /health`
- `GET /api/dashboard/bundle`

该 backend 只读取已经生成好的本地 `dashboard_bundle.json`。它不接受写入请求，不连接外部 API，
不做远程部署，也不实现多用户权限。后续 UI 可以直接读取 `/api/dashboard/bundle` 来展示报告、
仿真、工单、机队健康、audit 和 evidence refs。

本阶段不强制引入 ASGI server 运行依赖；测试通过 Starlette `TestClient` 验证只读 API。

## Minimal Web Dashboard UI

第三阶段新增 `GET /` 本地页面。页面会读取 `/api/dashboard/bundle`，展示 bundle id、
可用板块和本地 artifact refs。它不上传文件，不写入状态，不连接外部系统，只作为本地复核入口。

页面标题为 `无人机运维 Dashboard`，并明确展示 `offline-only`、只读和人工复核边界。

明确不包含：

- 真实无人机连接
- MAVLink command execution
- arm/disarm、takeoff、landing、RTL、mission execution、motor start
- firmware upload 或 flight-controller parameter writing
- PX4、ArduPilot、Gazebo、SITL 启动或连接
- 真实 fleet platform、CMMS、Jira、飞书、企业微信 API 调用
- 自动派单或自动执行维护动作
