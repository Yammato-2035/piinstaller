# Rescue Developer Profile — Agent Contract

## 1. Profile matrix

| Profil               | Agent installiert | Agent enabled | Auto Upload | Ziel |
| -------------------- | ----------------: | ------------: | ----------: | ---- |
| public_rescue        | optional/absent   |         false |       false | Nutzerrettung |
| beta_opt_in_future   |          optional |         false | nur explizit | redigierter Auszug |
| developer_local_lab  |                ja |          true |        true | lokaler Dev Server |
| dangerous_lab_future |                ja |         false |       false | später gated |

## 2. Harte Regeln

- Public Rescue startet **keinen** Upload
- Developer Agent nur im Developer-Profil aktiv
- Nur lokale/private Dev-Server-URLs im MVP
- SSH deaktiviert
- Keine Remote-Kommandos
- Keine Schreibaktionen, kein Backup/Restore
- Kein Token im Repo
- Kein Public Cloud Endpoint

## 3. Developer Environment

```
SETUPHELFER_DEV_AGENT_ENABLED=true
SETUPHELFER_DEV_AGENT_MODE=local_lab
SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000
SETUPHELFER_DEV_AGENT_COLLECT_STORAGE=true
SETUPHELFER_DEV_AGENT_COLLECT_BOOT=true
SETUPHELFER_DEV_AGENT_COLLECT_HARDWARE=true
```

## 4. Public Environment

```
SETUPHELFER_DEV_AGENT_ENABLED=false
SETUPHELFER_DEV_AGENT_MODE=public_rescue
SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=false
```

## 5. Abnahmekriterien (ohne ISO-Build)

- Developer-Profil unter `build/rescue/profiles/developer/` validiert
- Public-Profil blockiert Auto-Upload
- Guard-Script exit 0
- Unit-Tests grün
