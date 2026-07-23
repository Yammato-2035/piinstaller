SETUPHELFER Windows Diagnose / Live-Capture (ASUS G513QM)

Kein manueller Importbefehl noetig auf dem Stick.
Kein BitLocker aendern.

1) Optional: run-win11-setup-wrapper.cmd  (erzeugt Run-ID, startet Collector + Setup)
2) Oder: start-collector.cmd  vor/parallel zu Setup
3) Bei Ende/Hang: collect-final.cmd

Evidence landet unter SETUP_LOGS/asus-win11/<run_id>/
Nach Stick-Rueckgabe: scripts/rescue/import-asus-lab-runs auf dem Dev-Rechner.
