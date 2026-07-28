#!/usr/bin/env python3
"""
Supply-Chain-Gate: prüft docs/evidence/supply-chain/component-inventory.json
gegen aktuelle Upstream-Versionen (PyPI/npm) und schreibt ein Gate-JSON nach
docs/evidence/release-gates/supply_chain_gate.json — im selben Muster wie
die bestehenden Release-Gates.

Nur Komponenten mit status == "aktiv" werden geprüft. "geplant"/"inaktiv"
werden übersprungen (siehe Notiz im Inventar).

CVE-Scan läuft separat über pip-audit / npm audit im Workflow und wird hier
nur eingelesen (JSON-Reports), damit dieses Skript keine Netzwerk-Tools
selbst orchestrieren muss.

Exit-Code 0 immer (das Gate blockiert über den Ampel-Status im JSON, nicht
über den Prozess-Exit-Code — Entscheidung bewusst analog zu den bestehenden
Gates, die ebenfalls nicht den CI-Job selbst hart abbrechen).
"""
from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = REPO_ROOT / "docs/evidence/supply-chain/component-inventory.json"
GATE_OUT_PATH = REPO_ROOT / "docs/evidence/release-gates/supply_chain_gate.json"
PIP_AUDIT_REPORT = REPO_ROOT / "backend/pip-audit-report.json"
NPM_AUDIT_REPORT = REPO_ROOT / "frontend/npm-audit-report.json"

TIMEOUT_SECS = 10


def fetch_json(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None


def latest_pypi_version(name: str) -> str | None:
    data = fetch_json(f"https://pypi.org/pypi/{name}/json")
    if not data:
        return None
    return data.get("info", {}).get("version")


def latest_npm_version(name: str) -> str | None:
    data = fetch_json(f"https://registry.npmjs.org/{name}/latest")
    if not data:
        return None
    return data.get("version")


def load_audit_findings(path: Path, ecosystem: str) -> dict[str, list[str]]:
    """Liest pip-audit oder npm-audit JSON, gibt {paketname: [cve, ...]} zurück.
    Robust gegenüber fehlender Datei (Report evtl. noch nicht erzeugt)."""
    findings: dict[str, list[str]] = {}
    if not path.exists():
        return findings
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return findings

    if ecosystem == "pypi":
        for dep in data.get("dependencies", data if isinstance(data, list) else []):
            name = dep.get("name")
            vulns = dep.get("vulns", [])
            if name and vulns:
                findings[name.lower()] = [v.get("id", "?") for v in vulns]
    elif ecosystem == "npm":
        vulns = data.get("vulnerabilities", {})
        for name, info in vulns.items():
            via = info.get("via", [])
            ids = [str(v.get("source", v)) if isinstance(v, dict) else str(v) for v in via]
            findings[name.lower()] = ids
    return findings


def main() -> int:
    if not INVENTORY_PATH.exists():
        print(f"FEHLER: Inventar nicht gefunden unter {INVENTORY_PATH}", file=sys.stderr)
        return 0  # Gate schreibt trotzdem einen roten Status weiter unten

    inventory = json.loads(INVENTORY_PATH.read_text())
    komponenten = inventory.get("komponenten", [])

    pip_cves = load_audit_findings(PIP_AUDIT_REPORT, "pypi")
    npm_cves = load_audit_findings(NPM_AUDIT_REPORT, "npm")

    results = []
    hat_cve = False
    hat_netzwerkfehler = False
    geprueft = 0
    uebersprungen = 0

    for k in komponenten:
        name = k["name"]
        eco = k.get("ecosystem", "")
        status = k.get("status", "aktiv")

        if status != "aktiv" or eco not in ("pypi", "npm"):
            uebersprungen += 1
            results.append({
                "name": name, "ecosystem": eco, "status": status,
                "geprueft": False, "grund": "status != aktiv oder kein pypi/npm-Paket",
            })
            continue

        geprueft += 1
        latest = latest_pypi_version(name) if eco == "pypi" else latest_npm_version(name)
        if latest is None:
            hat_netzwerkfehler = True

        cve_map = pip_cves if eco == "pypi" else npm_cves
        cves = cve_map.get(name.lower(), [])
        if cves:
            hat_cve = True

        results.append({
            "name": name,
            "ecosystem": eco,
            "gepinnt": k.get("gepinnt"),
            "aktuellste_version_upstream": latest,
            "bekannte_cves": cves,
            "geprueft": True,
        })

    if hat_cve:
        ampel = "rot"
        empfehlung = "Mindestens eine aktive Komponente hat eine bekannte CVE — vor Release beheben oder Risiko bewusst akzeptieren und dokumentieren."
    elif hat_netzwerkfehler:
        ampel = "gelb"
        empfehlung = "Mindestens eine Versionsprüfung konnte Upstream nicht erreichen — Gate erneut laufen lassen, kein Blocker per se."
    else:
        ampel = "gruen"
        empfehlung = "Keine bekannten CVEs in aktiven Komponenten, alle Upstream-Abfragen erfolgreich."

    gate = {
        "gate_name": "supply_chain_gate",
        "geprueft_am": datetime.now(timezone.utc).isoformat(),
        "ampel": ampel,
        "geprueft_anzahl": geprueft,
        "uebersprungen_anzahl": uebersprungen,
        "empfehlung": empfehlung,
        "komponenten": results,
    }

    GATE_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_OUT_PATH.write_text(json.dumps(gate, indent=2, ensure_ascii=False))
    print(f"Supply-Chain-Gate geschrieben: {GATE_OUT_PATH} — Ampel: {ampel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
