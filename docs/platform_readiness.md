# v1.5.0 平台化准备

v1.5.0 的目标是为后续 v2.0.0 平台化打工程地基，但不引入真实平台连接。它把本地 workspace、report bundle、reviewer / approval model、offline adapter contract 和安全隐私治理清单先固化为可审计的离线契约。

## 本地 workspace / project

样例文件：

- `data/sample_platform/workspace_project.json`

它描述本地项目 ID、资产引用、报告包引用、reviewer roles 和数据保留策略。该文件只用于本地组织和审计，不代表多用户权限系统。

## Report bundle manifest

`build-report-bundle` 会扫描本地报告目录，写出 `report_bundle_manifest.json`：

```bash
python -m apps.cli.main build-report-bundle \
  --report-dir <tmp-report-dir> \
  --workspace-project-id workspace-local-demo \
  --bundle-id bundle-local-demo \
  --drone-id UAV-001 \
  --out <tmp>/report_bundle_manifest.json
```

该 manifest 只列出本地文件和 deterministic hash，不上传、不同步、不连接外部平台。

## reviewer / approval model

v1.5.0 引入 `ReviewerApproval` 契约，用于记录人工复核意见。它不是电子签章系统，也不会触发真实维修流程。所有 approval 输出默认 `human_review_required=true`。

## offline adapter contract

`OfflineAdapterContract` 用于声明未来适配器的允许操作和禁止操作。例如：

- 允许：`render_local_file`
- 禁止：`api_call`
- 禁止：`auto_dispatch`
- 禁止：`mavlink_command`

该契约只是边界说明，不会接入真实 CMMS、Jira、飞书、企业微信、fleet platform 或飞控系统。

## Platform readiness validation

```bash
python -m apps.cli.main validate-platform-readiness \
  --workspace data/sample_platform/workspace_project.json \
  --bundle data/sample_platform/report_bundle_manifest.json \
  --checklist data/sample_platform/platform_readiness_checklist.json \
  --out <tmp>/platform_readiness_validation.json
```

验证内容包括：

- workspace 与 report bundle 的引用关系。
- report bundle 是否包含本地文件清单。
- readiness checklist 是否存在。
- 安全边界是否声明 offline-only / advisory-only。
- offline adapter contract 是否明确禁止外部 API、自动派单和 MAVLink command。

## 数据保留与脱敏

v1.5.0 只使用仓库内已批准的 sample / sanitized fixture。后续如导入真实数据，必须先明确授权、脱敏状态、体积限制、保留周期和删除策略。当前版本不提交真实、敏感或未批准的二进制飞行日志。

## 安全边界

v1.5.0 不包含：

- 真实无人机连接
- MAVLink command execution
- arm/disarm、takeoff、landing、RTL、mission execution、motor start
- firmware upload
- flight-controller parameter writing
- PX4 / ArduPilot / Gazebo / SITL 启动或连接
- 真实 fleet platform API 调用
- 真实 CMMS、Jira、飞书、企业微信或其他维修系统 API 调用
- 自动派单
- 自动执行维护动作
- 真实、敏感或未批准的二进制飞行日志
