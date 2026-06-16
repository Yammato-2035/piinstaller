# Kommerzielle / private Säulen

**Stand:** 2026-06-16  
**Kontext:** Öffentliches GitHub-Repository (`Yammato-2035/piinstaller`)

## Private-only (dürfen nicht in Public GitHub)

1. **Cloud Backup** — kommerzielle Backup-Infrastruktur, Serverlogik, Kunden-Datenpfade
2. **Setuphelfer Cloud Edition Free** — strategisch geschützt trotz „Free“-Name; erst später aus stabilem Produkt ableiten
3. **Setuphelfer Cloud Edition Pro** — kommerzielle Edition, Lizenz-/Feature-Gates
4. **Telemetrieserver** — interne Ingest/Auswertung für Rettungsstick und Setuphelfer-Umgebung
5. **Diagnostikserver** — intern/kommerziell, Hardware-/Diagnose-Regeln
6. **Operator-Dashboard** — Cloud-Betreiber-/Kundenverwaltung (nicht lokales Dev-Cockpit)
7. **Lizenz-/Abo-/Billinglogik** — Enforcement, Subscriptions, Rechnungen
8. **Kommerzielle Service-Images / Blueprints** — z. B. `commercial-nextcloud-cloud`, `commercial-mailserver`
9. **Kommerzielle Cloud-Härtungsprofile** — `cloud-hardening-pro` und verwandte Profile
10. **Interne Telemetrie-Auswertung** — Aggregation, Korrelation, Kundenbezug
11. **Interne Diagnose-/Hardware-Regeln** — proprietäre Fingerprints, interne Matrizen
12. **Private Malware-/Security-Regelpakete** — kuratierte YARA/IOC-Pakete mit Geschäftsgeheimnis
13. **Private Plesk-/IONOS-Betreiberlogik** — Katalog-Submission, Produktiv-Tokens, SMTP/JWT

## Public-safe (erlaubt im öffentlichen Repo)

1. Setuphelfer Core (lokale Installation, soweit freigegeben)
2. Rettungsstick-Client und lokale UI (ohne interne Server)
3. Public-safe Backup/Restore/Verify-Grundlogik mit Safety-Gates
4. Redaction-Contracts und Client-Stubs
5. Telemetry-**Client**-Contracts ohne Serverlogik
6. Opt-in-/Datenschutztexte und Datenkategorien-Dokumentation
7. Neutrale OpenAPI-Contracts (Stubs, keine Secrets)
8. Lokale Test-Stubs ohne interne Serverlogik
9. Architekturhinweise ohne Geschäftsgeheimnisse
10. MSI/Windows-**Planungs**-Dokumente ohne Credential-Umgehung

## Pflichtentscheidungen

| Thema | Entscheidung |
|-------|--------------|
| Cloud Edition Free | **private-only** bis explizite Freigabe |
| Plesk Free Version | **nicht in diesem Lauf** — Future Plan only |
| Plesk Catalog Code | **nicht in diesem Lauf** |
| Telemetrieserver | intern/privat — nur Handoff + Client-Contract public |
| Diagnostikserver | intern/kommerziell — privat |
| Cloud Backup | kommerziell — privat |
| Dev-Dashboard (lokal) | public-safe **lokales** Entwickler-Cockpit; ≠ Operator-Dashboard |

## Gate

Vor jedem Commit: `./scripts/check-public-private-boundary.sh`  
Bei Block: **STOP** — Abschlussbericht `blocked_private_code_in_public_context`
