# Prompt 08 – Release-Gate (inkl. Monetarisierung)

STRICT MODE – RELEASE READINESS GATE

ZIEL:
Prüfen, ob Setuphelfer produktions- und monetarisierungsreif ist. Keine neuen Features.

PHASE 1 – PRÜFE DATEIEN:
- docs/roadmap/STATUS_MATRIX.md
- docs/testing/HARDWARE_TEST_MATRIX.md
- docs/testing/BACKUP_RESTORE_TEST_MATRIX.md
- docs/testing/RESCUE_STICK_TEST_MATRIX.md
- docs/testing/WEBSITE_TRANSPARENCY_TEST_MATRIX.md
- docs/testing/AFFILIATE_TRANSPARENCY_TEST_MATRIX.md
- docs/roadmap/RELEASE_READINESS_CHECKLIST.md
- docs/roadmap/MONETIZATION_READINESS_CHECKLIST.md

PHASE 2 – GATES:
Release nur grün wenn Mindesttests, Safety, Website, Affiliate, Legal und keine P0-Blocker – laut Checklisten.

PHASE 3 – OUTPUT:
- docs/evidence/release-gates/release_readiness_gate.json
- docs/evidence/release-gates/release_readiness_report.md
- docs/evidence/release-gates/backup_restore_release_gate.json
- docs/evidence/release-gates/hardware_release_gate.json
- docs/evidence/release-gates/website_release_gate.json
- docs/evidence/release-gates/affiliate_release_gate.json
- docs/evidence/release-gates/github_public_status_gate.json
- docs/evidence/release-gates/product_claims_review.md
- docs/evidence/release-gates/legal_release_gate.md

ABSCHLUSSBERICHT:
1. Release-Status: ready | review_required | blocked
2. P0/P1-Blocker
3. grüne / gelbe / rote / schwarze Bereiche
4. Empfehlung starten oder nicht
