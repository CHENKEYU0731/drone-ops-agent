from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import JSONResponse
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

    return Starlette(
        debug=False,
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/api/dashboard/bundle", dashboard_bundle, methods=["GET"]),
        ],
    )
