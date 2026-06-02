from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import FastAPI


def create_app(
    *,
    title: str,
    description: str,
    version: str,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[Any]] | None = None,
) -> FastAPI:
    """Erzeugt die FastAPI-App ohne Fachlogik."""
    return FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
    )

