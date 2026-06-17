# RS-F2B.1 Commit Test Result

| Test/Gate | Ergebnis | Bemerkung |
|-----------|----------|-----------|
| test_rescue_runtime_diagnostics_redaction_v1 | passed | 7/7 |
| test_rescue_evidence_store_v1 | passed | 3/3 |
| test_rescue_local_telemetry_queue_v1 | passed | 3/3 |
| test_rescue_telemetry_redaction_contract_v1 | passed | 3/3 |
| test_rescue_backup_plan_contract_v1 | passed | 10/10 |
| test_windows_ntfs_detection_contract_v1 | passed | |
| test_public_private_boundaries_v1 | passed | 6/6 (nach Restore unrelated docs) |
| test_module_boundaries_v1 | passed | |
| check-public-private-boundary.sh | passed | exit 0, staged |
| check-module-boundaries.sh | review_required | bekannt, nicht verschlechtert |

Gesamt: **46 passed**

Frontend npm test/build: nicht ausgeführt (kein zwingender CI-Blocker für diesen Commit-Lauf).
