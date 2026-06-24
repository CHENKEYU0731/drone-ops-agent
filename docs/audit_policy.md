# 审计策略

## 记录内容

每次 skill 执行记录：

- skill name
- skill version
- input file paths
- output file paths
- tools/functions called
- rules triggered
- timestamp
- human review required
- status

## 为什么需要审计

无人机运维建议会影响飞行安全和维护安全。审计记录让工程师能够追溯每个结论的输入、规则和输出，便于复核、复盘和持续改进。

## 从维护建议追溯到证据

维护建议包含 `evidence_refs`。每个证据引用记录 source type、source id、timestamp、field、measured value、threshold、rule id 和 description。报告的证据附录会汇总这些引用，帮助工程师从建议回到原始日志字段。
