"""
Boot correlation and root-cause ranking for multi-boot ASUS campaigns.

PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 Phases 19–20.

``rank_root_causes`` sorts candidates by confidence descending.
``correlate_boots`` classifies issue codes across boots into
persistent / intermittent / resolved / new problem lists.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def _confidence_of(candidate: Mapping[str, Any]) -> float:
    for key in ("confidence", "root_cause_confidence", "score"):
        if key in candidate and candidate[key] is not None:
            try:
                return float(candidate[key])
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def rank_root_causes(candidates: list[dict] | Sequence[Mapping[str, Any]] | None) -> list[dict]:
    """Return candidates sorted by confidence descending (stable for ties)."""
    items = [dict(c) for c in (candidates or []) if isinstance(c, Mapping)]
    # Stable sort: Python sort is stable; secondary key preserves original order via enumerate.
    indexed = list(enumerate(items))
    indexed.sort(key=lambda pair: (-_confidence_of(pair[1]), pair[0]))
    ranked: list[dict] = []
    for rank, (_idx, item) in enumerate(indexed, start=1):
        out = dict(item)
        out["rank"] = rank
        out["confidence"] = _confidence_of(item)
        ranked.append(out)
    return ranked


def _issue_codes_from_boot(boot: Mapping[str, Any]) -> set[str]:
    codes: set[str] = set()
    for key in ("issue_codes", "issues", "findings"):
        raw = boot.get(key)
        if raw is None:
            continue
        if isinstance(raw, (list, tuple, set)):
            for item in raw:
                if isinstance(item, Mapping):
                    code = item.get("issue_code") or item.get("code") or item.get("id")
                    if code:
                        codes.add(str(code))
                elif item:
                    codes.add(str(item))
        elif isinstance(raw, Mapping):
            for k, v in raw.items():
                if v:
                    codes.add(str(k))
        elif raw:
            codes.add(str(raw))
    single = boot.get("issue_code")
    if single:
        codes.add(str(single))
    return codes


def correlate_boots(boots: list[dict] | Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    """
    Correlate issue codes across ordered boots.

    Classification (by issue code):
    - persistent_problem: present in all boots
    - intermittent_problem: present in some but not all boots, and not
      exclusively previous-only or current-only relative to last two boots
      when that would already be resolved/new — specifically: appears in
      more than one boot but not every boot
    - resolved_problem: present in previous boots but not the current (last) boot
    - new_problem: present in current (last) boot but not in any previous boot

    Note: an issue present in all boots is only listed under persistent
    (not also intermittent). Resolved/new are relative to the last boot vs
    the union of earlier boots; intermittent covers non-universal codes that
    are neither exclusively new nor exclusively resolved when viewed across
    the full series (present in some boots, absent in others, and seen both
    before and on/after intermediate boots).
    """
    boot_list = [dict(b) for b in (boots or []) if isinstance(b, Mapping)]
    if not boot_list:
        return {
            "persistent_problem": [],
            "intermittent_problem": [],
            "resolved_problem": [],
            "new_problem": [],
            "boot_count": 0,
        }

    per_boot = [_issue_codes_from_boot(b) for b in boot_list]
    all_codes: set[str] = set()
    for s in per_boot:
        all_codes |= s

    current = per_boot[-1]
    previous_union: set[str] = set()
    for s in per_boot[:-1]:
        previous_union |= s

    persistent: list[str] = []
    intermittent: list[str] = []
    resolved: list[str] = []
    new: list[str] = []

    for code in sorted(all_codes):
        present_flags = [code in s for s in per_boot]
        present_count = sum(1 for f in present_flags if f)
        in_all = present_count == len(per_boot)
        in_current = code in current
        in_previous = code in previous_union

        if in_all:
            persistent.append(code)
            continue
        if in_previous and not in_current:
            resolved.append(code)
            continue
        if in_current and not in_previous:
            new.append(code)
            continue
        # Present in some boots, absent in others, and appeared in both
        # previous and current (or non-contiguous history) → intermittent.
        if 0 < present_count < len(per_boot):
            intermittent.append(code)

    return {
        "persistent_problem": persistent,
        "intermittent_problem": intermittent,
        "resolved_problem": resolved,
        "new_problem": new,
        "boot_count": len(boot_list),
    }
