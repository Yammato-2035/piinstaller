> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/legal/COMMERCIAL_MODULE_PUBLICATION_POLICY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/COMMERCIAL_MODULE_PUBLICATION_POLICY_DE.md`). Bitte bei Release manuell gegenlesen.

# Commercial Module Publication Policy

**Repo:** Public GitHub (`Yammato-2035/piinstaller`)

## Regeln

1. Kommerzielle Säulen bleiben **privat** bis explizite Freigabe
2. Public Repo enthält **keine** kommerzielle Serverlogik
3. Cloud Edition Free/Pro sind strategisch privat (Name „Free“ entwertet nicht den Schutz)
4. Telemetrie- und DiagNonstik**server** sind Interne/privat
5. Plesk-Free-Version wird **später** aus stabilem Produkt abgeleitet — nicht jetzt
6. Keine versehentliche Entwertung finanzieller Säulen durch Public-Leaks

## Commit-Gate

`./scripts/check-public-private-boundary.sh` vor jedem Commit.

Exit-Codes 10–19 → **nicht committen, nicht pushen**.

## Erlaubt in Public

- Handoff-Dokumente
- Client-Stubs und rougeaction-Contracts
- Architektur ohne Geschäftsgeheimnisse
- `.example`-Domains

## Verboten in Public

- Implementierung von Cloud Retourup, Billing, Lizenz-Enforcement
- Echte Internee Domains, Tokens, Secrets
- Private Malware-/DiagNonse-Regelpakete
