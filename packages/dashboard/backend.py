from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from packages.drone_schemas import read_json_file


def create_dashboard_app(*, bundle_path: Path) -> Starlette:
    bundle_path = Path(bundle_path)

    async def health(_request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "mode": "offline-read-only",
                "human_review_required": True,
            }
        )

    async def dashboard_bundle(_request) -> JSONResponse:
        payload = read_json_file(bundle_path)
        return JSONResponse(payload)

    async def dashboard_page(_request) -> HTMLResponse:
        return HTMLResponse(_DASHBOARD_HTML)

    return Starlette(
        debug=False,
        routes=[
            Route("/", dashboard_page, methods=["GET"]),
            Route("/health", health, methods=["GET"]),
            Route("/api/dashboard/bundle", dashboard_bundle, methods=["GET"]),
        ],
    )


_DASHBOARD_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>无人机运维 Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5d6d7e;
      --line: #d6dbdf;
      --panel: #ffffff;
      --bg: #f4f6f7;
      --accent: #117864;
      --warn: #b03a2e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      padding: 20px 28px;
    }
    main {
      display: grid;
      gap: 16px;
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }
    h1 {
      font-size: 24px;
      margin: 0;
      letter-spacing: 0;
    }
    h2 {
      font-size: 16px;
      margin: 0 0 8px;
      letter-spacing: 0;
    }
    .subtle {
      color: var(--muted);
      margin: 4px 0 0;
    }
    .grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 16px;
    }
    .value {
      font-size: 20px;
      font-weight: 700;
      margin: 0;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 28px;
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid var(--line);
      background: #fdfefe;
      font-size: 13px;
    }
    .badge.ok { color: var(--accent); }
    .badge.warn { color: var(--warn); }
    ul {
      margin: 8px 0 0;
      padding-left: 18px;
    }
    code {
      overflow-wrap: anywhere;
      color: var(--muted);
    }
  </style>
</head>
<body>
  <header>
    <h1>无人机运维 Dashboard</h1>
    <p class="subtle">本地只读、offline-only、advisory-only，不连接真实无人机或外部平台。</p>
  </header>
  <main>
    <div class="grid">
      <section>
        <h2>Bundle</h2>
        <p class="value" id="bundle-id">加载中</p>
        <p class="subtle">数据源：<code>/api/dashboard/bundle</code></p>
      </section>
      <section>
        <h2>安全边界</h2>
        <span class="badge ok">只读</span>
        <span class="badge ok">离线</span>
        <span class="badge warn">需要人工复核</span>
      </section>
    </div>
    <section>
      <h2>可用板块</h2>
      <ul id="sections"></ul>
    </section>
    <section>
      <h2>本地 artifact</h2>
      <ul id="artifacts"></ul>
    </section>
  </main>
  <script>
    const flatten = (obj, prefix = "") => Object.entries(obj || {}).flatMap(([key, value]) => {
      const name = prefix ? `${prefix}.${key}` : key;
      if (value && typeof value === "object" && !Array.isArray(value)) return flatten(value, name);
      return [[name, value]];
    });

    fetch("/api/dashboard/bundle")
      .then((response) => response.json())
      .then((bundle) => {
        document.getElementById("bundle-id").textContent = bundle.bundle_id || "未命名 bundle";
        const sections = document.getElementById("sections");
        (bundle.sections || []).forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          sections.appendChild(li);
        });
        const artifacts = document.getElementById("artifacts");
        flatten(bundle.artifacts || {}).forEach(([name, value]) => {
          const li = document.createElement("li");
          li.innerHTML = `<strong>${name}</strong>: <code>${value ?? "未提供"}</code>`;
          artifacts.appendChild(li);
        });
      });
  </script>
</body>
</html>
"""
