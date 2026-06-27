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

## Rule Pack Validation CLI

第二阶段新增：

```bash
python -m apps.cli.main validate-rule-pack \
  --rule-pack data/sample_rule_packs/offline_default_rules.json \
  --out /tmp/rule_pack_validation.json
```

`rule_pack_validation.json` 是确定性输出，包含：

- `status`
- `rule_pack`
- `counts`
- `scopes`
- `findings`
- `safety_boundary`
- `human_review_required`

验证逻辑会暴露缺失 evidence fields、缺失 inputs 等可审计问题。当前验证只读取本地 JSON，
不加载真实硬件、不连接外部平台，也不改变任何规则执行结果。

## Skill Version Registry

第三阶段新增：

```bash
python -m apps.cli.main list-skills \
  --rule-pack data/sample_rule_packs/offline_default_rules.json \
  --out /tmp/skill_registry.json
```

```bash
python -m apps.cli.main list-rule-packs \
  --rule-pack data/sample_rule_packs/offline_default_rules.json \
  --out /tmp/rule_packs.json
```

`skill_registry.json` 记录本地 core CLI skill 名称、版本、分类，以及可审计 rule pack reference。
这些信息只是离线治理元数据，不触发真实规则执行、飞控连接或外部系统调用。
