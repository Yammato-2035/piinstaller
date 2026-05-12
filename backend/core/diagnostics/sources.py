from __future__ import annotations

from core.diagnostics.models import DiagnosticsAnalyzeRequest


def normalized_signals(req: DiagnosticsAnalyzeRequest) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in (req.signals or {}).items():
        if isinstance(v, bool):
            out[k] = "true" if v else "false"
        elif v is None:
            out[k] = "null"
        else:
            out[k] = str(v).strip().lower()
    return out


def normalized_question(req: DiagnosticsAnalyzeRequest) -> str:
    return (req.question or "").strip().lower()
