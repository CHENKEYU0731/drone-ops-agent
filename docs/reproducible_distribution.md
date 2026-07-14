# 可复现分发

`v2.4.0` 为项目增加一条可检查、可重复的本地分发路径。它解决的是“另一台开发机能否按同样步骤安装、验证和查看成果”，不改变无人机运维分析的业务规则。

## 环境诊断

```bash
python scripts/check_environment.py --out environment.json
```

输出使用稳定 JSON 结构，包含项目版本、Python 版本、核心/可选依赖状态和安全边界。输出不记录用户名、仓库绝对路径、访问令牌或其他本地敏感信息。

## 直接依赖约束

- `constraints/runtime.txt`：核心运行时直接依赖。
- `constraints/dev.txt`：运行时与开发/测试直接依赖。
- `constraints/optional-parsers.txt`：可选 PX4/ArduPilot parser 直接依赖。
- `constraints/release.txt`：构建工具直接依赖。

约束文件没有伪装成完整供应链 lockfile。它们固定项目直接依赖，传递依赖仍由 Python 包索引解析；因此每次发布还需要保存构建产物 SHA-256 并通过 CI。

## 确定性发布包

```bash
python scripts/build_release_bundle.py --out dist/release
```

输出：

- `drone-ops-agent-2.4.0.zip`
- `drone-ops-agent-2.4.0.zip.sha256`
- ZIP 内的 `distribution_manifest.json`
- ZIP 内的 `SHA256SUMS`

脚本只读取 Git 已跟踪文件，按路径排序，固定 ZIP 时间戳和权限，拒绝符号链接，并排除虚拟环境、构建目录、缓存、外部 ULog 缓存和 Python bytecode。同一提交运行两次应得到相同 SHA-256。构建必须从 Git checkout 执行，避免把未跟踪的本地文件或凭据意外打包。

## Windows 一条命令验收

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_release.ps1
```

该脚本在系统临时目录创建虚拟环境，按约束安装依赖，运行环境诊断、`pytest`、demo 生成、wheel/sdist 构建、wheel 安装和 CLI smoke test，最后生成确定性 ZIP。临时环境在结束时清理，发布产物默认写入 `dist/release-check`。

依赖安装和构建阶段可能访问 Python 包索引；这是显式的开发/发布操作，不属于项目运行时。安装后的分析与验证仍为 offline-only、advisory-only 和 human-review-required，不连接真实无人机，不执行 MAVLink command，不启动 PX4、ArduPilot、Gazebo 或 SITL，也不写飞控参数或接入真实维修系统。
