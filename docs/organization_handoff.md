# v1.8.0 组织级离线交接包

v1.8.0 在 v1.5-v1.7 的平台化准备基础上，新增一个本地 `OrganizationHandoffPackage`。它把 workspace、report bundle、dataset registry、offline adapter registry、approval packet 和 platform readiness checklist 收成一个可审计的组织级交接包 manifest。

这个交接包只记录本地 artifact reference，不上传文件、不调用真实平台、不连接真实无人机、不接入真实维修系统，也不自动派单。它的用途是让后续 v2.0.0 平台化前，先有一份稳定、可验证、可人工复核的离线交接清单。

## 契约

`OrganizationHandoffArtifact` 描述单个本地交接材料：

- `artifact_id`
- `artifact_type`
- `path`
- `required`
- `description`
- `human_review_required`

`OrganizationHandoffPackage` 描述交接包整体：

- `package_id`
- `version`
- `workspace_project_id`
- `artifact_refs`
- `reviewer_roles`
- `safety_boundary`

示例 fixture：

```text
data/sample_handoff/organization_handoff_package.json
```

## CLI

验证交接包：

```bash
python -m apps.cli.main validate-handoff-package \
  --package data/sample_handoff/organization_handoff_package.json \
  --out <tmp>/handoff_validation.json
```

输出：

- `handoff_validation.json`
- `audit/organization-handoff-validation-*.json`

## 验证重点

`validate-handoff-package` 会检查：

- required artifact 的本地路径存在。
- package 声明 reviewer roles。
- package 声明 `offline_only=true`。
- package 声明 `advisory_only=true`。
- package 声明不连接真实平台。
- package 声明不自动派单。
- artifact 默认需要人工复核。

## 安全边界

v1.8.0 不包含：

- 真实无人机连接。
- MAVLink command execution。
- arm/disarm、takeoff、landing、RTL、mission execution、motor start。
- firmware upload。
- flight-controller parameter writing。
- PX4、ArduPilot、Gazebo、SITL 或外部仿真器启动或连接。
- 真实 fleet platform、CMMS、Jira、飞书、企业微信或其他维修系统 API 调用。
- 自动派单。
- 自动执行维修动作。
- 真实、敏感或未批准的二进制飞行日志。

