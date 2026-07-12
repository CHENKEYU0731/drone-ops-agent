# Platform Readiness Index

`platform_readiness_index.json` 是 v1.9.0 的离线平台能力索引，用来把 v0.7.0 到 v1.8.0 已经完成的本地质量门禁、报告、数据集、评估、适配器、审批和交接能力收成一个可复核的清单。

它不是生产平台目录，也不是接入真实无人机、真实维修系统或真实 fleet platform 的入口。它只描述本仓库中已经存在的 offline-only / advisory-only 能力，以及每项能力的推荐本地验证命令和输出文件。

## 数据契约

v1.9.0 新增两个 schema：

- `PlatformReadinessCapability`：描述一个本地能力的 `capability_id`、标题、版本、推荐命令、输出引用、安全说明和 `human_review_required=true`。
- `PlatformReadinessIndex`：描述一组能力、发布前检查项和整体安全边界。

样例文件位于：

```text
data/sample_platform/platform_readiness_index.json
```

当前样例索引覆盖：

- `dashboard-bundle`
- `dataset-registry`
- `eval-suite`
- `fleet-health`
- `offline-adapters`
- `organization-handoff`
- `platform-readiness`
- `rule-pack-versioning`

## 验证命令

使用 `validate-platform-index` 生成确定性的 `platform_index_validation.json` 和 audit 记录：

```bash
python -m apps.cli.main validate-platform-index \
  --index data/sample_platform/platform_readiness_index.json \
  --out <tmp>/platform_index_validation.json
```

当结果为 `REVIEW_REQUIRED` 时，命令仍会写出 validation JSON 和 audit，但会返回非零退出码，便于 CI 或脚本阻止错误放行。

输出包括：

- `platform_index_validation.json`
- `audit/platform-readiness-index-validation-*.json`

验证会检查：

- index 是否声明 `offline_only=true`、`advisory_only=true` 和 `human_review_required=true`。
- index 是否禁止真实外部平台连接和自动派单。
- 每个 capability 是否包含推荐命令和输出引用。
- 每个 capability 是否默认要求人工复核。
- 每个 capability 是否声明 `offline-only` 和 `advisory-only` 安全说明。
- 发布前检查项是否包含 `pytest`。

## 安全边界

本能力只做本地离线索引和质量门禁，不连接真实无人机，不执行 MAVLink command execution，不执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start、firmware upload 或 flight-controller parameter writing。

本能力也不启动或连接 PX4、ArduPilot、Gazebo、SITL 或外部仿真器，不调用真实 fleet platform、CMMS、Jira、飞书、企业微信或其他真实维修系统 API，不自动派单，不上传文件，也不提交真实、敏感或未经批准的二进制飞行日志。

所有结论都必须保持 advisory-only，并默认需要人工复核。
