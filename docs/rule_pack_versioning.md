# v1.3.0 规则包和 Skill 版本管理

`v1.3.0 - Rule Pack and Skill Versioning` 的目标是让项目的规则、skill 和审计元数据更可复用、
可验证、可追溯。它不改变任何真实执行能力，只为离线规则治理建立稳定结构。

## Rule Pack Contract Baseline

第一阶段新增：

- `RulePackScope`
- `RulePackRule`
- `RulePack`
- `data/sample_rule_packs/offline_default_rules.json`

`RulePackRule` 描述单条规则的：

- `rule_id`
- `version`
- `scope`
- `description`
- `severity`
- `inputs`
- `thresholds`
- `evidence_fields`
- `human_review_required`

`RulePack` 描述一个可审计规则包的：

- `pack_id`
- `name`
- `version`
- `scope`
- `rules`
- `source_refs`
- `safety_boundary`

## 安全边界

规则包只是本地离线元数据，不会：

- 连接真实无人机
- 执行 MAVLink command
- 执行 arm/disarm、takeoff、landing、RTL、mission execution、motor start
- 上传 firmware 或写 flight-controller parameter
- 启动或连接 PX4、ArduPilot、Gazebo、SITL
- 调用真实 fleet platform、CMMS、Jira、飞书或企业微信 API
- 自动派单或执行维护动作
