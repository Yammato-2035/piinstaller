# RS-F2B.1 Dirty Tree Classification

| Datei | Kategorie | Staging | Grund |
|-------|-----------|--------:|-------|
| backend/core/rescue_* (RS-F2B.1) | rs_f2b1_backend_fix | ja | Kernfix |
| backend/api/handlers, routes | rs_f2b1_backend_fix | ja | API |
| frontend/src/rescue/* | rs_f2b1_frontend_fix | ja | UI |
| scripts/rescue-live/* | rs_f2b1_script | ja | WLAN/Evidence |
| backend/tests/test_rescue_* | rs_f2b1_test | ja | Unit-Tests |
| docs/evidence/rescue-stick/RS_F2B1_* | rs_f2b1_evidence | ja (ohne WIFI_LOG_SCAN) | Evidence |
| docs/roadmap/STATUS_MATRIX.md | roadmap_status | ja | Matrix |
| VERSION, config/version.json, package.json | version_file | ja | 1.9.4.0 |
| telemetry_server_*.py | private_only | nein | Telemetrie-Server private |
| docs/architecture/*V2*, TELEMETRY_SERVER* | private_only | nein | Private Strategie |
| docs/evidence/runtime-results/* | generated_build_artifact | nein | lsblk/blkid Rohdaten |
| RS_F2B1_WIFI_LOG_SCAN.txt | secret_or_sensitive | nein | /home/volker Pfade |
| RS_F2S_*_SCAN.txt | secret_or_sensitive | nein | Roh-Scan-Pfade |
| docs/faq, ROADMAP_2026 (restored) | unrelated_dirty | nein | Gate-Blocker, restored |
| ckb-next | unrelated_dirty | nein | Submodul |
