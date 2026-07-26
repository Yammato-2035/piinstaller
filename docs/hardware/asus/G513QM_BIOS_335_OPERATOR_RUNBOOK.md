# G513QM BIOS 335 — Operator Runbook

**Cursor does not flash BIOS.** Operator only, after A/B/C baseline on current BIOS.

## Preconditions

1. Controls A/B/C baseline documented on current BIOS (expected 331-class unless already updated).
2. BitLocker recovery key secured offline.
3. AC adapter connected.
4. Model binding: **G513QM** only (reject other ROG files).
5. File from **official ASUS** support only; record SHA256 locally before flash.
6. No Setuphelfer / no automatic flash / no Secure Boot auto-change.

## Steps

1. Confirm BIOS version in BIOS setup screen (photo).
2. Download ASUS BIOS 335 package for G513QM from ASUS Support.
3. `sha256sum` the ZIP/CAP; store under evidence `bios_335/`.
4. Follow ASUS EZ Flash / MyASUS instructions exactly.
5. After update: re-run Control A → B → C with **new run IDs**; never mix pre/post results.

## Status values

`not_required` · `recommended_after_baseline` · `ready_for_operator` · `blocked_wrong_model` · `blocked_file_unverified` · `operator_completed`
