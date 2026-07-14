# 能力矩阵

| 能力 | 输入 | 主要输出 | 验证证据 | 当前边界 |
| --- | --- | --- | --- | --- |
| CSV/JSON 日志解析 | 本地 sample/sanitized 文件 | 统一 telemetry records | parser unit/integration tests | 不读取实时链路 |
| PX4 ULog / ArduPilot BIN | 本地 mock 或显式缓存文件 | parser metadata、飞行摘要 | mock fixtures、3 个上游 ULog 兼容案例 | 不启动 PX4/ArduPilot，不声称真实准确率 |
| 异常与诊断 | 飞行摘要、资产信息 | anomalies、diagnosis | `evidence_refs`、audit | 规则型假设，需人工复核 |
| 维护建议 | diagnosis、资产信息 | maintenance recommendations | 证据链、优先级、audit | 不执行维修动作 |
| 仿真验证 | offline/mock scenario/result | `simulation_run.json` | 14 场景 matrix、逐规则结果 | 不启动 Gazebo/SITL |
| 运维报告 | 摘要、诊断、建议、仿真、工单 | Markdown/PDF | `report_validation.json` | PASS 不代表飞行授权 |
| 证据索引 | anomalies、diagnosis、maintenance、audit | `evidence_index.json` | broken/missing refs findings | 只验证本地材料 |
| 工单草稿 | maintenance recommendations | `DRAFT` JSON/Markdown | work-order validation | 不接入真实 CMMS/Jira，不自动派单 |
| 机队健康 | 多资产 sample manifest | fleet summary/report | aggregation tests | 不接入真实 fleet platform |
| 本地 Dashboard | 报告与机队成果 | 只读 bundle/页面 | backend/bundle tests | 无写操作、无控制接口 |
| 平台质量门禁 | dataset/adapter/approval/handoff/index | validation JSON | schema、readiness tests | 仅离线 contract 验证 |
| 评测与案例研究 | golden/mock cases | accuracy/coverage/false alarm/miss metrics | 15 个固定案例 | 不代表真实世界统计泛化 |
| 可复现分发 | Git checkout、固定直接依赖 | wheel/sdist、源码 ZIP、SHA-256 | clean venv、CI 3.11/3.12 | 传递依赖不是完整 lockfile |
| 作品展示包 | 仓库内 sample/mock/sanitized 数据 | PDF、JSON、Markdown、PNG、ZIP | manifest、每文件 SHA-256 | 不包含外部二进制日志或凭据 |

所有能力默认保持 `human_review_required=true`，并遵守 offline-only、advisory-only 安全边界。系统不连接真实无人机，不执行任何 MAVLink command。
