# PI-RS-MSI-RETEST-001 — Import und Auswertung nach MSI-Boot

## Nach dem Operator-Boot-Retest (PI-RS-MSI-RETEST-002)

### 1. SETUP_LOGS mounten

```bash
# Typisch bereits unter:
/media/<user>/SETUP_LOGS
```

Nur lesen/kopieren — nicht formatieren, nicht löschen.

### 2. Dateien importieren

Ziel (lokal, nicht blind committen):

```text
docs/evidence/rescue/imports/pi-rs-msi-retest-001/
```

Empfohlene Kandidaten (redacted/summary):

| Datei | Zweck |
|-------|-------|
| `setuphelfer/diagnostics/latest/00-meta.txt` | Boot-Metadaten, Produkt, Kernel |
| `setuphelfer/evidence/msi-rs011b/api-version.json` | Runtime-Version |
| `setuphelfer/evidence/msi-rs011b/storage-discovery.json` | Storage |
| `setuphelfer/evidence/msi-rs011b/disk-discovery.json` | Disks |
| `setuphelfer/evidence/msi-rs011b/rescue-health.json` | Health/Ampel |
| `setuphelfer/evidence/msi-rs011b/msi-killer-e2500-detection.json` | LAN |
| `setuphelfer/evidence/msi-rs011b/collector-summary.json` | Session-Zusammenfassung |

### 3. Redaction

- Keine Rohlogs mit Secrets, MACs, Seriennummern, IPs committen
- `92-dmesg-full.txt`, `journal-*` nur lokal archivieren oder stark redigieren
- Vor Commit: `rg` auf `password`, `Bearer`, `Authorization`, private keys

### 4. Versionen prüfen

- `project_version` / `rescue_version` = erwartete Stick-Version (**1.10.0.12** für aktuellen Plan)
- Abweichung zu Workspace **1.9.19.4** dokumentieren (kein Fehler per se)

### 5. Erwartete Dateien

| Erwartet | Pflicht |
|----------|---------|
| `diagnostics/latest/00-meta.txt` | ja |
| `evidence/msi-rs011b/api-version.json` | ja |
| `storage-discovery.json` | ja |
| `disk-discovery.json` | ja |
| `operator-steps.jsonl` | optional |

Fehlende Dateien im Abschlussbericht PI-RS-MSI-RETEST-002 auflisten.

### 6. Entscheidung

| Ergebnis | Bedeutung |
|----------|-----------|
| **passed** | MSI-Retest Kriterien erfüllt |
| **partial / review_required** | Einzelne Checks offen |
| **failed** | Boot/Runtime blockiert |
| **rebuild / repack_required** | Payload-Drift oder fehlende Runtime → PI-RS-REPACK-001 |
