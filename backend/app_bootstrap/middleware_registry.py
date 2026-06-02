from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

HttpMiddleware = Callable[[Any, Callable[..., Any]], Any]


def register_middlewares(app: FastAPI, middlewares: list[HttpMiddleware]) -> int:
    """Registriert HTTP-Middlewares in definierter Reihenfolge."""
    count = 0
    for mw in middlewares:
        app.middleware("http")(mw)
        count += 1
    return count

