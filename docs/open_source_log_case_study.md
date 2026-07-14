# 开源上游日志兼容性案例研究

v2.3.0 在没有导师授权真实日志的情况下，引入一条可审计的公开数据替代路径。这里的目标是验证 parser 对上游 ULog 的兼容性，不是宣称真实飞行异常检测准确率。

## 数据来源

当前注册表使用 `PX4/pyulog` BSD-3-Clause 仓库 commit `3cf17793f14709713ab297d3743314c658874068` 中的 3 个 ULog fixture：

- `sample_log_small.ulg`
- `sample_logging_tagged_and_default_params.ulg`
- `sample_px4_events.ulg`

注册表位于 `data/open_source_logs/registry.json`，每个来源都声明 repository、固定 commit、source path、许可证、字节数和 SHA-256。

上游仓库将这些文件作为 parser 测试 fixture 提供，但公开元数据不足以证明它们来自真实外场飞行。因此全部记录 `real_world_flight_verified=false`。

## 显式获取

安装 PX4 可选依赖：

```bash
pip install -e .[px4]
```

根据注册表中的固定 `download_url`，使用浏览器或系统下载工具将三个文件放入 `data/open_source_logs/cache/`。例如 PowerShell 可使用：

```powershell
New-Item -ItemType Directory -Force data/open_source_logs/cache
curl.exe -L -o data/open_source_logs/cache/sample_log_small.ulg <registry-download-url>
```

项目不内置网络客户端。注册表验证会限制来源为 `raw.githubusercontent.com` 的 HTTPS 固定 commit URL、单文件不超过 10 MB，并要求许可证 URL 固定到同一 commit。案例研究开始前会重新验证本地缓存的文件名、大小和 SHA-256。缓存目录被 Git 忽略。

## 离线分析

```bash
python -m apps.cli.main run-open-log-case-studies \
  --registry data/open_source_logs/registry.json \
  --cache-dir data/open_source_logs/cache \
  --drone-id UAV-OPEN-SOURCE \
  --out <tmp-open-log-dir>
```

案例研究命令本身不联网。它会再次校验缓存文件，然后调用 `px4-ulog` parser，输出：

- `open_log_case_study.json`
- `open_log_case_study.md`
- `audit/open-source-log-case-study-*.json`

当前 3 个来源分别解析出 21、52、157 条统一记录。

## 已确认限制

- 飞控启动相对时间映射到 Unix epoch，不代表真实 UTC 时间。
- 前四路 actuator 输出仅作为四电机兼容性映射，未证明一定对应真实电机顺序。
- 某些日志没有可解释的链路质量字段，parser 会使用默认值并写出 warning。
- parser 兼容性通过不等于异常诊断准确率，更不等于真实飞行安全验证。

## 安全边界

项目运行时代码不下载或上传任何内容。外部获取与项目分析严格分离；分析过程保持 offline-only、advisory-only 和 `human_review_required=true`，不连接真实无人机、飞控、仿真器、维修系统或 fleet platform，不执行 MAVLink command、自动派单、固件上传或飞控参数写入。
