# RS-001 FAT32 ESP Payload Update — False Success Failure Analysis

**Datum:** 2026-06-09  
**Evidence-Run:** `fat32_esp_payload_update_20260609_165016`  
**Git HEAD (Analyse):** `aeee57c`

---

## Zusammenfassung

Payload update reported success despite write errors.

| Feld | Wert |
|------|------|
| **Actual squashfs hash (forensic)** | `921c3e23bfbeb99a6295b80be5f8b5d40b55994019b0e614fef633138c6bdfe7` |
| **Expected old hash** | `921c3e23bfbeb99a6295b80be5f8b5d40b55994019b0e614fef633138c6bdfe7` |
| **Expected new hash** | `ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a` |
| **Actual state** | **old** |
| **Retest allowed** | **no** |

---

## Beobachtete Schreibfehler (Operator-Lauf)

```text
mkdir: /tmp/tmp.../.sqtmp kann nicht angelegt werden: Keine Berechtigung
cp: .sqtmp/filesystem.squashfs.new kann nicht angelegt werden
mv: .sqtmp/filesystem.squashfs.new nicht gefunden
PermissionError: setuphelfer/rescue/evidence.json
```

Trotzdem meldete `result.json` fälschlich `payload_update_status: success`.

---

## Forensische Bewertung

1. `old_payload_hashes.json` zeigt **alten** Stick-Hash (`921c3e23…`) — SquashFS wurde vor dem fehlgeschlagenen Copy gelesen.
2. `copy.log` enthält `NEW_SQUASHFS_SHA256=ac95ebc3…` — das ist der Hash der **Quelldatei**, nicht des Sticks nach Copy.
3. `verify.log` fehlt im Evidence-Ordner; Verify prüfte nur Layout/Größe, **keinen** SquashFS-Hash.
4. Root-owned FAT-Mount: `mkdir`/`cp`/`mv` ohne `sudo` schlugen fehl.
5. Python `Path.write_text()` auf Mount schlug mit `PermissionError` fehl; Pipeline `python | tee` maskierte den Exit-Code (`PIPESTATUS`).

**Conclusion:** SquashFS auf dem Stick wurde **nicht** aktualisiert. Der gemeldete Erfolg war ein Fake-Success.

---

## Korrekturmaßnahmen (dieser Lauf)

- Evidence `result.json` + `fat32_esp_payload_update_latest.json` auf `failed` / `review_required` korrigiert.
- `update-fat32-esp-live-payload.sh`: `sudo` für Mount-Writes, `run_step`, Hash-Gate nach Copy, kein `python | tee`.
- `verify-fat32-esp-rescue-usb.sh`: optional `--expected-squashfs-sha256`.
- Retest-Handoff gesperrt bis erneuter Payload-Update-Lauf mit fixiertem Skript.

---

## Read-only Stick-Probe (Agent)

Agent-Umgebung ohne sudo-TTY: direkter RO-Mount nicht möglich. Bewertung basiert auf Evidence-Forensik und `old_payload_hashes.json` (konsistent mit **old**).
