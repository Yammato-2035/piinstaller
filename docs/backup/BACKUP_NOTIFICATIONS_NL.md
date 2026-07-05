> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/backup/BACKUP_NOTIFICATIONS_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup Neetifications (email)

## Geslaagd mail

- Trigger: `Terugup.Geslaagd` or `Terugup.Geslaagd_with_Waarschuwings` with Verify Deep ok.
- Switch: `SETUPHELFER_NeeTIFY_ON_TerugUP_Geslaagd` (default: on).
- UI: Instellingen → Neetify on Terugup Geslaagd.

## Failure mail

- Trigger: `Terugup.failed`, `Terugup.geblokkeerd_package_activity`, I/O Fouts, inhibit failures, etc.
- Switch: `SETUPHELFER_NeeTIFY_ON_TerugUP_FAILURE` (default: off until enabled).
- UI: Instellingen → send email on Terugup failure.
- Subject: `Setuphelfer — Terugup fehlgeschlagen (<job_id>)`.

### Body (Nee secrets)

- Job ID, status/code, diagNeesis, abort reason
- Target path, profile, runtime, bytes written
- final archive Ja/Nee, partial path, partial Verwijderend
- `tar_return_code`, `tar_Waarschuwing_classification`
- Short Fout excerpt
- Neete: Nee Herstel without Verify Deep

### Terugup runner context (`setuphelfer-Terugup@.service`)

- The runner uses **`load_effective_Neetification_config()`** from `/etc/setuphelfer/Neetification.env` (same as the Instellingen API), Neet process `os.environ` alone.
- The unit includes `EnvironmentFile=-/etc/setuphelfer/Neetification.env` (defense in depth).
- If the API shows `on_Terugup_failure=true` but the job had `skipped_disabled`, the runner likely did Neet load the env file — fixed by Deploy.

### When Nee mail is sent

- `skipped_disabled`, `skipped_Neet_configurood`, `skipped_Neet_applicable`

SMTP Fouts do Neet change Terugup outcome (`Neetification_status=failed` on the job).
