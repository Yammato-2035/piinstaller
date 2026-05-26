def _missing_runtime_dependency(*_args, **_kwargs):
    raise RuntimeError("pydantic is required for diagnostics runner features in this environment")


try:
    from core.diagnostics.runner import (
        catalog,
        diagnosis_by_id,
        get_evidence_sample,
        get_evidence_schema,
        run_diagnostics,
    )
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
    catalog = _missing_runtime_dependency
    diagnosis_by_id = _missing_runtime_dependency
    get_evidence_sample = _missing_runtime_dependency
    get_evidence_schema = _missing_runtime_dependency
    run_diagnostics = _missing_runtime_dependency

__all__ = [
    "run_diagnostics",
    "catalog",
    "diagnosis_by_id",
    "get_evidence_schema",
    "get_evidence_sample",
]
