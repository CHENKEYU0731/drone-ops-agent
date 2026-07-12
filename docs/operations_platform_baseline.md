# Operations Platform Baseline

`operations_platform_baseline.json` 是 v2.0.0 的离线组织级运维平台基线 manifest。它把前面版本已经完成的本地能力组织成一个可验证的“平台视图”：报告、仿真验证、机队健康、dashboard bundle、规则包、数据集、审批、交接、平台 readiness index 和工单草稿。

它不是 SaaS 平台，也不是连接真实无人机、真实维修系统或真实 fleet platform 的入口。v2.0.0 的目标是证明项目已经具备组织级离线运维决策材料的结构、验证门禁和发布检查路径。

## 数据契约

v2.0.0 新增两个 schema：

- `OperationsPlatformModule`：描述一个本地平台模块的 artifact refs、验证命令、预期输出、复核角色和安全说明。
- `OperationsPlatformBaseline`：描述组织级离线平台基线、模块清单、release checks 和整体安全边界。

样例文件位于：

```text
data/sample_platform/operations_platform_baseline.json
```

当前样例 baseline 覆盖：

- `dashboard-bundle`
- `dataset-registry`
- `eval-suite`
- `fleet-health`
- `organization-handoff`
- `platform-readiness`
- `platform-readiness-index`
- `rule-pack-versioning`
- `work-order-drafts`

## 验证命令

使用 `validate-operations-platform` 生成确定性的 `operations_platform_validation.json` 和 audit 记录：

```bash
python -m apps.cli.main validate-operations-platform \
  --baseline data/sample_platform/operations_platform_baseline.json \
  --out <tmp>/operations_platform_validation.json
```

当结果为 `REVIEW_REQUIRED` 时，命令仍会写出 validation JSON 和 audit，但会返回非零退出码，便于 CI 或脚本阻止错误放行。

输出包括：

- `operations_platform_validation.json`
- `audit/operations-platform-validation-*.json`

验证会检查：

- baseline 是否声明 `offline_only=true`、`advisory_only=true` 和 `human_review_required=true`。
- baseline 是否禁止真实无人机连接、MAVLink command execution、真实外部平台连接、真实维修系统、自动派单和仿真器启动。
- 每个 module 是否包含 artifact refs、validation commands、expected outputs 和 reviewer roles。
- 每个 module 是否默认要求人工复核。
- 每个 module 是否声明 `offline-only`、`advisory-only` 和 `human-review-required` 安全说明。
- release checks 是否包含 `pytest` 和 `validate-operations-platform`。

## 安全边界

本能力只做本地离线 manifest 和质量门禁，不连接真实无人机，不执行 MAVLink command execution，不执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start、firmware upload 或 flight-controller parameter writing。

本能力也不启动或连接 PX4、ArduPilot、Gazebo、SITL 或外部仿真器，不调用真实 fleet platform、CMMS、Jira、飞书、企业微信或其他真实维修系统 API，不自动派单，不上传文件，也不提交真实、敏感或未经批准的二进制飞行日志。

所有结论都必须保持 advisory-only，并默认需要人工复核。
