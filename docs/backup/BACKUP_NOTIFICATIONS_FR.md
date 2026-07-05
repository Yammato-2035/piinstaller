> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/backup/BACKUP_NOTIFICATIONS_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup Nontifications (email)

## Succès mail

- Trigger: `Retourup.Succès` or `Retourup.Succès_with_Avertissements` with Verify Deep ok.
- Switch: `SETUPHELFER_NonTIFY_ON_RetourUP_Succès` (default: on).
- UI: Paramètres → Nontify on Retourup Succès.

## Failure mail

- Trigger: `Retourup.failed`, `Retourup.bloqué_package_activity`, I/O Erreurs, inhibit failures, etc.
- Switch: `SETUPHELFER_NonTIFY_ON_RetourUP_FAILURE` (default: off until enabled).
- UI: Paramètres → send email on Retourup failure.
- Subject: `Setuphelfer — Retourup fehlgeschlagen (<job_id>)`.

### Body (Non secrets)

- Job ID, status/code, diagNonsis, abort reason
- Target path, profile, runtime, bytes written
- final archive Oui/Non, partial path, partial Supprimerd
- `tar_return_code`, `tar_Avertissement_classification`
- Short Erreur excerpt
- Nonte: Non Restauration without Verify Deep

### Retourup runner context (`setuphelfer-Retourup@.service`)

- The runner uses **`load_effective_Nontification_config()`** from `/etc/setuphelfer/Nontification.env` (same as the Paramètres API), Nont process `os.environ` alone.
- The unit includes `EnvironmentFile=-/etc/setuphelfer/Nontification.env` (defense in depth).
- If the API shows `on_Retourup_failure=true` but the job had `skipped_disabled`, the runner likely did Nont load the env file — fixed by Déploiement.

### When Non mail is sent

- `skipped_disabled`, `skipped_Nont_configurouge`, `skipped_Nont_applicable`

SMTP Erreurs do Nont change Retourup outcome (`Nontification_status=failed` on the job).
