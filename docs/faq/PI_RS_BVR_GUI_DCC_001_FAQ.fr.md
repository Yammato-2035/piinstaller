# PI-RS-BVR-GUI-DCC-001 FAQ (FR)

Date : **2026-07-21**  
Task : **PI-RS-BVR-GUI-DCC-001**  
Statut : **`implemented_pending_physical_retest`**  
Payload cible : **1.10.1.1**

KB : [GUI_HTTP_SERVER_FAILED_FR.md](../knowledge-base/rescue-stick/GUI_HTTP_SERVER_FAILED_FR.md) · [BVR_STATUS_AND_FALLBACK_FR.md](../knowledge-base/rescue-stick/BVR_STATUS_AND_FALLBACK_FR.md)

---

## 1. Qu'est-ce que PI-RS-BVR-GUI-DCC-001 ?

Tache pour la runtime HTTP GUI (serveur ASCII-safe, readiness avant Chromium), quatre locales pour la page de progression auto-E2E, et visibilite statut/drift DCC — sans modifier le noyau BVR gele (backup/verify/restore).

## 2. Quel est le statut actuel ?

**`implemented_pending_physical_retest`** : implementation et tests unitaires dans le workspace ; retest physique MSI avec payload **1.10.1.1** encore en attente. La GUI n'est **pas** confirmee physiquement.

## 3. Pourquoi la GUI n'etait-elle pas visible au baseline ?

Run de reference `e2e-rescue-msi-20260721-232222-ba58c7a7` : serveur HTTP Python inline en echec (`SyntaxError`, non-ASCII dans literal bytes) → `http_server_failed`. Chromium n'a pas demarre ; watchdog → TUI.

## 4. Le BVR a-t-il reussi malgre tout ?

Oui. Backup, verify, restore, manifeste et auto-shutdown **passed**. Statut global : **`passed_with_gui_fallback`**.

## 5. Qu'a-t-on implemente pour corriger ?

- Serveur dedie `setuphelfer-rescue-ui-http-server` (ASCII-safe)
- Gate readiness via `GET /health.json`
- Chromium apres readiness uniquement
- Locales de/en/fr/nl pour `auto-e2e-progress.html`
- Statut DCC et matrice de drift version

## 6. Le BVR continue-t-il si la GUI echoue ?

Oui. Noyau BVR et GUI decouples. Echec GUI ne bloque pas backup/verify/restore.

## 7. Quelle version de payload est cible ?

**1.10.1.1** (baseline **1.10.1.0**). Repack stick et test physique requis pour feu vert GUI.

## 8. Quelles langues pour la GUI de progression ?

`de-DE`, `en-US`, `fr-FR`, `nl-NL` — via cmdline `setuphelfer_locale=` ou variable d'environnement.

## 9. Quand Chromium demarre-t-il ?

Seulement si `/health.json` renvoie HTTP **200**, `status=ready`, index present, i18n valide (page progression). Un port ouvert seul ne suffit pas.

## 10. Prochaine etape ?

Construire payload **1.10.1.1**, retest MSI GE63, importer evidence vers `physical_msi_result.json`. Voir [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md).

---

## Voir aussi

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
