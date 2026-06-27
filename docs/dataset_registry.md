# v1.6.0 数据集与案例注册表

v1.6.0 新增本地 dataset / case registry，用来把仓库里的 sample logs、report validation case、simulation case、eval case、fleet manifest 和 platform readiness bundle 统一登记起来。

该能力只做本地文件索引和质量门禁，不会下载数据，不会上传数据，不会连接真实无人机、真实平台或真实维修系统。

## 核心契约

`DatasetCase` 描述单个本地案例：

- `case_id`
- `case_type`
- `source_refs`
- `sanitized_status`
- `capabilities`
- `recommended_commands`
- `expected_outputs`
- `safety_boundary`

`DatasetRegistry` 描述一组本地案例：

- `registry_id`
- `version`
- `cases`
- `source_refs`
- `safety_boundary`

样例注册表：

- `data/sample_datasets/registry.json`

## 验证命令

```bash
python -m apps.cli.main validate-datasets \
  --registry data/sample_datasets/registry.json \
  --out <tmp>/dataset_validation.json
```

验证内容包括：

- registry schema 能加载。
- 每个 `source_refs` 指向本地存在的文件。
- `sanitized_status` 属于允许值，例如 `sanitized_sample` 或 `mock_sample`。
- 每个 case 声明 `recommended_commands`。
- 每个 case 声明 `expected_outputs`。
- registry 和 case 均声明 offline-only / advisory-only 安全边界。
- 所有输出默认 `human_review_required=true`。

## 当前覆盖的案例类型

当前 sample registry 覆盖：

- `flight_log`
- `report_directory`
- `simulation_case`
- `eval_case`
- `fleet_manifest`
- `platform_readiness`

## 数据安全边界

v1.6.0 只登记仓库内已有的 sample / mock / sanitized fixtures。后续若导入真实数据，必须先确认授权、脱敏状态、体积限制、保留周期和删除策略。

本版本不包含：

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
