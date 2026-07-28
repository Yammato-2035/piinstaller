#!/usr/bin/env python3
"""
Gate-Freshness-Check (Paket 3, E-08).

Prüft alle *.json-Dateien unter docs/evidence/release-gates/ auf
Aktualität, primär anhand des Git-Commit-Datums der Datei (nicht des
JSON-Inhalts, da viele Gates kein eigenes Datumsfeld führen).

Schreibt docs/evidence/release-gates/GATE_FRESHNESS_REPORT.json.
Ändert NIEMALS den Inhalt bestehender Gate-Dateien.

Nutzung:
    python3 scripts/gate_freshness_check.py [--repo-root .]

Exit-Code 0 immer — die Bewertung liegt im Report, nicht im Exit-Code
(analog zum Supply-Chain-Gate, siehe Paket 1b).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_policy(repo_root: Path) -> dict:
    policy_path = repo_root / "scripts" / "gate_freshness_policy.json"
    if not policy_path.exists():
        # Sinnvolle Defaults, falls Policy-Datei fehlt
        return {
            "schwelle_kritisch_tage": 14,
            "schwelle_standard_tage": 30,
            "verdacht_kopiert_abweichung_tage": 7,
            "kritische_gates": [],
            "ausschluss_muster": ["README.md"],
        }
    return json.loads(policy_path.read_text())


def git_last_modified(repo_root: Path, file_path: Path) -> datetime | None:
    """Datum des letzten Commits, der diese Datei verändert hat.
    Gibt None zurück, wenn kein Git verfügbar oder Datei nicht getrackt ist
    (z.B. neu erstellt, noch nicht committet)."""
    try:
        rel = file_path.relative_to(repo_root)
    except ValueError:
        rel = file_path
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(rel)],
            cwd=repo_root, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = result.stdout.strip()
    if not out:
        return None
    try:
        return datetime.fromisoformat(out)
    except ValueError:
        return None


def embedded_timestamp(data: dict) -> datetime | None:
    for key in ("generated", "geprueft_am", "date", "stand", "timestamp"):
        val = data.get(key)
        if isinstance(val, str):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    return None


def is_excluded(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    gates_dir = repo_root / "docs" / "evidence" / "release-gates"
    if not gates_dir.exists():
        print(f"FEHLER: {gates_dir} nicht gefunden", file=sys.stderr)
        return 0

    policy = load_policy(repo_root)
    krit_tage = policy["schwelle_kritisch_tage"]
    std_tage = policy["schwelle_standard_tage"]
    verdacht_tage = policy["verdacht_kopiert_abweichung_tage"]
    kritische_gates = set(policy.get("kritische_gates", []))
    ausschluss = policy.get("ausschluss_muster", [])

    now = datetime.now(timezone.utc)
    ergebnisse = []
    git_verfuegbar = git_last_modified(repo_root, gates_dir / "README.md") is not None \
        or (repo_root / ".git").exists()

    for f in sorted(gates_dir.glob("*.json")):
        if is_excluded(f.name, ausschluss) or f.name == "GATE_FRESHNESS_REPORT.json":
            continue

        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            data = {}

        git_dt = git_last_modified(repo_root, f)
        embed_dt = embedded_timestamp(data)

        # Primäres Datum: Git, Fallback: eingebettetes Feld
        ref_dt = git_dt or embed_dt
        quelle = "git" if git_dt else ("eingebettetes_feld" if embed_dt else "keines")

        alter_tage = (now - ref_dt).days if ref_dt else None
        ist_kritisch = f.name in kritische_gates
        schwelle = krit_tage if ist_kritisch else std_tage

        if alter_tage is None:
            status = "UNBEKANNT"
        elif alter_tage > schwelle:
            status = "STALE-KRITISCH" if ist_kritisch else "STALE"
        else:
            status = "OK"

        verdacht_kopiert = False
        if git_dt and embed_dt:
            abweichung = abs((git_dt - embed_dt).days)
            if abweichung > verdacht_tage:
                verdacht_kopiert = True

        ergebnisse.append({
            "datei": f.name,
            "kritisch": ist_kritisch,
            "git_commit_datum": git_dt.isoformat() if git_dt else None,
            "eingebettetes_datum": embed_dt.isoformat() if embed_dt else None,
            "datumsquelle": quelle,
            "alter_tage": alter_tage,
            "schwelle_tage": schwelle,
            "status": status,
            "verdacht_kopiert_statt_neu_generiert": verdacht_kopiert,
        })

    anzahl_stale_kritisch = sum(1 for r in ergebnisse if r["status"] == "STALE-KRITISCH")
    anzahl_stale = sum(1 for r in ergebnisse if r["status"] == "STALE")
    anzahl_unbekannt = sum(1 for r in ergebnisse if r["status"] == "UNBEKANNT")
    anzahl_verdacht = sum(1 for r in ergebnisse if r["verdacht_kopiert_statt_neu_generiert"])

    if anzahl_stale_kritisch > 0:
        gesamt_ampel = "rot"
    elif anzahl_stale > 0 or anzahl_unbekannt > 0:
        gesamt_ampel = "gelb"
    else:
        gesamt_ampel = "gruen"

    report = {
        "schema": "setuphelfer.evidence.v1",
        "id": "gate_freshness_report",
        "geprueft_am": now.isoformat(),
        "git_verfuegbar": git_verfuegbar,
        "ampel": gesamt_ampel,
        "anzahl_geprueft": len(ergebnisse),
        "anzahl_stale_kritisch": anzahl_stale_kritisch,
        "anzahl_stale": anzahl_stale,
        "anzahl_unbekannt": anzahl_unbekannt,
        "anzahl_verdacht_kopiert": anzahl_verdacht,
        "hinweis": "Ändert keine bestehenden Gate-Dateien. Git-Commit-Datum ist primäre Quelle, da viele Gates kein eigenes Zeitstempel-Feld führen.",
        "gates": ergebnisse,
    }

    out_path = gates_dir / "GATE_FRESHNESS_REPORT.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Gate-Freshness-Report geschrieben: {out_path}")
    print(f"Ampel: {gesamt_ampel} | stale-kritisch: {anzahl_stale_kritisch} | stale: {anzahl_stale} | unbekannt: {anzahl_unbekannt} | verdacht-kopiert: {anzahl_verdacht}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
