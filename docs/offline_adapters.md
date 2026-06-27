# v1.7.0 离线适配器与审批工作流

v1.7.0 延续 `v1.5.x Platform Readiness` 路线，把平台化前需要的适配器边界和人工审批流程先固化为本地、可审计、可重复验证的契约。

本版本不接入真实 fleet platform、CMMS、Jira、飞书、企业微信或任何真实维修系统；也不连接真实无人机、飞控、MAVLink endpoint、PX4、ArduPilot、Gazebo 或 SITL。所有输出都是 offline-only、advisory-only，并且默认 `human_review_required=true`。

## 契约

`OfflineAdapterRegistry` 用来登记本地 mock/offline adapter contract。每个 adapter 只能描述允许的本地文件渲染或导出动作，并显式列出禁止动作：

- `api_call`
- `auto_dispatch`
- `mavlink_command`
- `real_platform_connection`

示例 fixture：

```text
data/sample_adapters/offline_adapter_registry.json
```

`ApprovalPacket` 用来记录某个本地输出对象的人工复核包，例如 report bundle、work order draft bundle 或 fleet summary export。它包含：

- `subject_ref`
- `required_roles`
- `approvals`
- 每条 approval 的 reviewer、role、decision、rationale
- offline/advisory safety boundary

示例 fixture：

```text
data/sample_approvals/approval_packet.json
```

## CLI

验证 adapter registry：

```bash
python -m apps.cli.main validate-adapters \
  --registry data/sample_adapters/offline_adapter_registry.json \
  --out <tmp>/adapter_validation.json
```

验证 approval packet：

```bash
python -m apps.cli.main validate-approvals \
  --packet data/sample_approvals/approval_packet.json \
  --out <tmp>/approval_validation.json
```

两个命令都会写出确定性的 JSON validation output，并在输出目录下写入 `audit/*.json`。validation 通过只代表本地结构、证据边界和人工复核字段满足离线质量门禁，不代表真实平台发布、真实派单或真实维修授权。

## 验证重点

`validate-adapters` 会检查：

- registry 和 adapter 均声明 `offline_only=true`。
- registry 和 adapter 均声明 `advisory_only=true`。
- adapter 禁止 `api_call`、`auto_dispatch` 和 `mavlink_command`。
- adapter 声明不连接真实平台。
- adapter 默认需要人工复核。

`validate-approvals` 会检查：

- approval packet 有明确的 `subject_ref`。
- `required_roles` 被 approval 覆盖。
- 每条 approval 有 reviewer、role、decision 和 rationale。
- 每条 approval 默认 `human_review_required=true`。
- approval packet 保持 offline/advisory safety boundary。

## 安全边界

v1.7.0 不包含：

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
