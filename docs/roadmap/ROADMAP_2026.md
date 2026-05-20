# Roadmap 2026 – Setuphelfer (Stabilisierung)

**Fokus:** Produktions- und Monetarisierungsreife **ohne** neuen Funktionsumfang.

## Quartalsrichtung

1. **Q2 2026:** Transparenz (Repo + GitHub), Backup/Restore/Verify belastbar, erste Hardware-Evidence.
2. **Q3 2026:** Rescue-Stick read-only (Boot, Erkennung, Verify, Bericht), Monolith-Audit abgeschlossen, kleine refactor-fähige Schritte geplant.
3. **Q4 2026:** Website-Status live, Affiliate-Kennzeichnung, Release-Gates für Markt/UG.

## Explizit nicht in dieser Phase

- Cloudserver Edition, Plesk-Modul, Modulshop  
- neue Premium-Features, neue Distributionen  
- Enterprise / White-Label  
- große UI-Redesigns  

## Leitlinie

> Erst Backup. Dann Änderungen.

## BR-001-Pivot (2026-05-20)

- **Release-Gate Desktop Privat:** **BR-001-OFFLINE** über Setuphelfer-Rettungsstick (stillstehendes Dateisystem, externes Ziel).
- **BR-001-LIVE** (Full-Root auf laufendem Desktop): **experimentell**, keine weiteren Live-Retries als Gate (tar/apt/Timeshift/Chrome-Evidence).
- **Cloudserver:** Snapshot + inkrementell — eigene Matrix, nicht BR-001-LIVE.
- Architektur: `docs/architecture/BR-001_GATE_STRATEGY_DE.md`

## Verweise

- Detailphasen: Nutzer-Spezifikation „Setuphelfer – ToDo-Liste“ (Phase 0–8)  
- Matrizen: `docs/testing/`  
- Ampel: `docs/roadmap/STATUS_MATRIX.md`  
- Öffentlicher Text: `docs/roadmap/PUBLIC_STATUS_PAGE.md`  
