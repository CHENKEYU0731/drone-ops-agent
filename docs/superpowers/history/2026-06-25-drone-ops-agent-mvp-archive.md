# Legacy Drone Ops Agent MVP Branch Archive

日期：2026-06-25

## 结论

`feat/drone-ops-agent-mvp` 是早期 MVP 历史线，已被后续主线发布历史替代。为避免覆盖或倒退当前主线，该分支不再 PR、不再 merge，仅保留为本地历史参考。

后续如果需要恢复其中某些内容，只允许从当前 `main` 新建分支，并以 cherry-pick、手动迁移或重写增量实现的方式处理，不能直接 merge unrelated history。

## 旧分支

- 分支名：`feat/drone-ops-agent-mvp`
- 当前用途：本地历史参考
- 集成状态：不再作为 PR 或 merge 来源

## 旧分支包含的提交

- `950191f docs: Add drone ops agent MVP design`
- `c07ee18 feat: Add offline drone ops agent MVP`
- `72cd788 fix: Harden drone ops MVP acceptance gaps`
- `afd0fe1 ci: Add GitHub Actions MVP validation`

## 当时的本地验证

该分支在归档检查时仍可通过早期 MVP 验证：

- `pytest`：`19 passed`
- `python -m apps.cli.main run-mvp ...`：通过
- `drone-ops run-mvp ...`：通过

运行产物、audit 随机产物和缓存文件均为 ignored，未进入提交。

## 安全扫描结果

安全扫描未发现真实无人机控制能力。命中项仅包括：

- 安全禁止说明
- 未来只读导入说明
- 既有飞行模式文本，例如 `LAND`

未发现以下能力的实现：

- arm/disarm
- 启动电机
- 起飞、降落、返航
- 航线执行
- 上传固件
- 写飞控参数
- MAVLink command execution

## 不再 PR 的原因

该分支与当前 `main` 没有 merge base。检查时出现：

```text
fatal: main...HEAD: no merge base
```

当前 `main` 已发布到 `v0.6.0`，包含后续 preflight、monitoring、PDF、PX4 ULog、ArduPilot BIN、offline SITL validation、真实样例日志验证基础设施和 release notes 等大量内容。

直接将 `feat/drone-ops-agent-mvp` 作为 PR 合入当前 `main`，会把早期 MVP 历史线重新引入当前发布主线，存在覆盖或倒退当前主线的风险。因此该分支不适合作为 PR 合入当前 `main`。

## 后续处理原则

- 保留 `feat/drone-ops-agent-mvp` 作为本地历史参考。
- 不再 push 该分支。
- 不再基于该分支创建 PR。
- 不直接 merge unrelated history。
- 如需恢复旧分支中的个别内容，应从最新 `main` 新建分支，并做最小增量迁移。
