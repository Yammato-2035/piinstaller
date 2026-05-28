# Rescue ISO — Retry nach Chroot-Cleanup (Klassifikation)

**Datum:** 2026-05-28

| Feld | Wert |
|------|------|
| `classification` | **build_not_retried** |
| `cleanup_success` | false (Operator ausstehend) |
| `error_code` | RESCUE-BUILD-CHROOT-CLEANUP-001 |
| `rescue_status` | blocked (kein full-green) |

Build-Retry bewusst **nicht** gestartet: Cleanup-Preconditions (sudo rm chroot) nicht erfüllt.

JSON: `rescue_iso_retry_after_chroot_cleanup_classification_latest.json`
