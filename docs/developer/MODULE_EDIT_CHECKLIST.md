# Modul-Checkliste (bei jeder Modulbearbeitung)

**Verwendung:** Vor und nach Änderungen an einem Modul abarbeiten; Ergebnisse im Bericht ([CHANGE_REPORT_TEMPLATE.md](./CHANGE_REPORT_TEMPLATE.md)) festhalten.  
**Vollständige Regeln:** [CURSOR_WORK_RULES.md](./CURSOR_WORK_RULES.md).

---

## Checkliste

- [ ] **Modul identifiziert** (Name, Routen/Seiten-ID, Backend-Paket/Pfad).
- [ ] **Arbeitsumgebung geprüft** (Repo-Pfad, verfügbare Befehle ohne neue Installation).
- [ ] **Reale Prüfungen dokumentiert** (was gelaufen ist / was nicht geht / nur statisch).
- [ ] **Modul nutzt i18n** wo vorgesehen (`useTranslation` / `i18n.t`, Keys unter `frontend/src/locales/`).
- [ ] **Harte sichtbare UI-Texte** im geänderten Bereich erfasst (Liste oder „keine neuen“).
- [ ] **Toasts / Modals / Statusmeldungen** auf Lokalisierung geprüft.
- [ ] **Backend-Texte** für dieses Modul (Fehler, Diagnose), die im UI erscheinen, benannt (Sprache/Lücken).
- [ ] **Diagnose-Logik** vorhanden oder bewusst nicht zutreffend (API-Pfad, Fallback).
- [ ] **Doku / FAQ / Wissensbasis** – Matrix in CURSOR_WORK_RULES durchgegangen; Anpassung oder Begründung für „nein“.
- [ ] **Version & Changelog** – [VERSIONING.md](./VERSIONING.md); `config/version.json` + `CHANGELOG.md` + ggf. In-App-Changelog.
- [ ] **Restliste** offener Punkte (i18n-Rest, Tests, technische Schuld) erstellt.

---

## Kurzreferenz für Cursor-Prompts

> „Vor Änderung: `docs/developer/MODULE_EDIT_CHECKLIST.md` abarbeiten; Bericht nach `docs/developer/CHANGE_REPORT_TEMPLATE.md`; Regeln: `docs/developer/CURSOR_WORK_RULES.md`.“
