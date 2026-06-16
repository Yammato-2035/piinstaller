# Rescue Boot-Menü i18n

**Stand:** 2026-06-08 · Version **1.7.11.0**

## Locales

| Locale | Datei | Staging-Ziel |
|--------|-------|--------------|
| `de` | `frontend/src/rescue/i18n/de.json` | `/opt/setuphelfer-rescue/i18n/de.json` |
| `en` | `frontend/src/rescue/i18n/en.json` | `/opt/setuphelfer-rescue/i18n/en.json` |

## Schlüsselstruktur

```
title, subtitle, hint, menuPrompt
menu.<id>.title / menu.<id>.subtitle
status.medium / status.network / status.telemetry / status.optional / status.off
footer.help / footer.language / footer.network / footer.debug / footer.reboot / footer.shutdown / footer.select
lang
```

## Menü-IDs (datengetrieben)

| id | DE title | EN title |
|----|----------|----------|
| `system_analyze` | System analysieren | Analyze system |
| `backup_create` | Backup erstellen | Create backup |
| `backup_verify` | Backup prüfen | Verify backup |
| `restore` | Wiederherstellen | Restore |
| `malware_scan` | Malware prüfen | Check malware |
| `cloudserver_manage` | Cloudserver verwalten | Manage cloud server |
| `settings` | Einstellungen | Settings |

## Verbotene Markenphrasen (UI-Scan)

Nicht in neuem Rescue-UI-Code:

- `Rescue Stick`
- `Rettungsstick`

Programmname bleibt **Setuphelfer** (`title` in beiden Locales).

## Komponenten-Regeln

- `RescueStartCenter.tsx` nutzt nur `tPath(dict, key)` — keine literalen Menüstrings
- `rescueMenuItems.ts` referenziert nur `titleKey` / `subtitleKey`
- Neue Locale: JSON-Datei unter `frontend/src/rescue/i18n/<locale>.json` + Staging-Erweiterung in `stage-rescue-graphical-assets.sh`
