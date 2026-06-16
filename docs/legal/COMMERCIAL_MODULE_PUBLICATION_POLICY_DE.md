# Commercial Module Publication Policy

**Repo:** Public GitHub (`Yammato-2035/piinstaller`)

## Regeln

1. Kommerzielle Säulen bleiben **privat** bis explizite Freigabe
2. Public Repo enthält **keine** kommerzielle Serverlogik
3. Cloud Edition Free/Pro sind strategisch privat (Name „Free“ entwertet nicht den Schutz)
4. Telemetrie- und Diagnostik**server** sind intern/privat
5. Plesk-Free-Version wird **später** aus stabilem Produkt abgeleitet — nicht jetzt
6. Keine versehentliche Entwertung finanzieller Säulen durch Public-Leaks

## Commit-Gate

`./scripts/check-public-private-boundary.sh` vor jedem Commit.

Exit-Codes 10–19 → **nicht committen, nicht pushen**.

## Erlaubt in Public

- Handoff-Dokumente
- Client-Stubs und Redaction-Contracts
- Architektur ohne Geschäftsgeheimnisse
- `.example`-Domains

## Verboten in Public

- Implementierung von Cloud Backup, Billing, Lizenz-Enforcement
- Echte interne Domains, Tokens, Secrets
- Private Malware-/Diagnose-Regelpakete
