"""Rescue remote control (local_lab phase 1): allowlisted runbooks only, no shell."""

__all__ = ["router"]


def __getattr__(name: str):
    if name == "router":
        from rescue_remote.routers import router

        return router
    raise AttributeError(name)
