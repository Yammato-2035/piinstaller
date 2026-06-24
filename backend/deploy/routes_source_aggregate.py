"""Deploy route source aggregation for contract tests after sub-router extraction."""

from __future__ import annotations

from pathlib import Path

_DEPLOY = Path(__file__).resolve().parent


def read_deploy_routes_aggregate() -> str:
    """Monolith routes.py plus all deploy/routes_*.py sub-routers."""
    parts = [_DEPLOY / "routes.py"]
    parts.extend(sorted(_DEPLOY.glob("routes_*.py")))
    return "".join(p.read_text(encoding="utf-8") for p in parts)


def read_deploy_sub_router(filename: str) -> str:
    return (_DEPLOY / filename).read_text(encoding="utf-8")


def extract_deploy_route_block(path_fragment: str, *, window: int = 1200) -> str:
    """Handler source for one deploy route (stops before the next @router.*)."""
    src = read_deploy_routes_aggregate()
    markers = (
        f'@router.post("/runner/manual-runtime/{path_fragment}"',
        f'@router.post("/runner/{path_fragment}"',
        f'@router.post("/{path_fragment}"',
        f'@router.get("/runner/manual-runtime/{path_fragment}"',
        path_fragment,
    )
    start = -1
    for marker in markers:
        start = src.find(marker)
        if start >= 0:
            break
    if start < 0:
        return ""
    end = len(src)
    for end_marker in ("@router.post", "@router.get", "@router.delete"):
        pos = src.find(end_marker, start + 12)
        if start < pos < end:
            end = pos
    block = src[start:end]
    return block if block else src[start : start + window]
