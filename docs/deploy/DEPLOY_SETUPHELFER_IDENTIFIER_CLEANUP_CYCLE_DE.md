# Deploy Setuphelfer Identifier Cleanup Cycle (DE)

Zyklus 1: Plan aus `setuphelfer_safe_rewrite_plan.json` (max. 100 Eintraege, Scope nur Backend/Frontend/Scripts/Config/systemd und definierte package/tauri-Dateien), Apply mit Backup unter `legacy-backups/`, Postcheck mit neuem Inventory und Consistency-Check.

Keine Evidence-/History-Pfade, keine Runtime-Ausfuehrung, Version bleibt 1.7.0.
