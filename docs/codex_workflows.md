# Codex 后续工作流

可以把以下任务继续交给 Codex：

- 增加 PX4 ULog 只读解析支持。
- 增加 ArduPilot BIN 只读解析支持。
- 增加 MAVLink 遥测只读导入。
- 扩展 `monitor-replay` 规则和样例 telemetry 数据，但必须保持离线 advisory-only，不得连接真实无人机或执行真实动作。
- 增加 SITL 仿真验证，但保持真实硬件隔离。
- 扩展 PDF 报告高级排版、表格渲染和模板版本管理。
- 增加 Web Dashboard。
- 增加工单系统或 CMMS 集成。
- 增加失败运行审计。
- 增加规则阈值配置文件。
- 扩展飞行前检查规则和样例，但必须保持 advisory-only，不得接入真实飞控控制动作。

每个任务都应先更新安全边界和测试，再实现代码。
