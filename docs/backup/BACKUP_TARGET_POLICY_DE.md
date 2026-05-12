# Backup-Zielrichtlinie (Setuphelfer) — Deutsch

## Grundsatz

- Backups sollen **bevorzugt auf externen Datenträgern** liegen, nicht auf Root-, Boot- oder Systempartitionen.
- Setuphelfer **zerstört keine bestehenden Daten**, **formatiert nicht automatisch** und **partitioniert nicht** im Namen des Nutzers.
- Wenn kein **eindeutig sicheres externes** Ziel ermittelt werden kann, bleibt Backup **blockiert** (`blocked` / `review_required`).
- Wenn der Dienstnutzer ein Ziel **nicht traversieren** oder **nicht beschreiben** darf, wird **keine** stille Umleitung auf interne Pfade vorgenommen — es ist eine **explizite Betreiber-/Nutzerfreigabe** nötig (siehe Diagnose **STORAGE-PROTECTION-006** / API-Code **`backup.target_traverse_denied`** nach Aktualisierung des Backends).

## Priorität externer Medien (absteigend)

1. Externe **NVMe** (z. B. USB-NVMe-Gehäuse, `TRAN`/Modell plausibel)
2. Externe **SSD** (SATA/NVMe im USB-Gehäuse)
3. Externe **HDD**
4. **USB-Stick** (typisch kleiner, langsamer; nur wenn eindeutig unkritisch und ausreichend Platz)
5. **SD-Karte** (nur wenn eindeutig extern, rw, passendes Dateisystem und ausreichend Platz)

**Nicht** als Backup-Ziel: Root-Dateisystem (`/`), interne System-NVMe, Boot/EFI, Windows-Systempartitionen, Pfade ausschließlich unter `/tmp`, `/home`, `/var` ohne separates externes Blockgerät, **readonly**-Medien, Medien ohne ausreichenden **freien** Platz.

## Strategischer Mount-Pfad (Dokumentation)

Der Pfad **`/media/setuphelfer/setuphelfer-back`** ist als **konventionelles Ziel** gedacht, **ausschließlich**, wenn er auf einem **gewählten externen Blockgerät** liegt (Mount zeigt auf `/dev/...` außerhalb der Systemplatte).

- **Verboten:** denselben Pfad als normales Verzeichnis auf dem Root-Dateisystem anzulegen oder interne NVMe als Träger zu nutzen.
- **Kein automatisches Bind-Mount** und **keine** automatische ACL-/Rechteänderung ohne ausdrückliche Freigabe.
- Wenn das Medium bereits unter z. B. **`/media/<Benutzer>/setuphelfer-back`** gemountet ist, erfolgt **keine** automatische Umdeutigung — Abstimmung mit dem Betreiber, ob der strategische Pfad Umzug/Mount/Bind erfordert.

## API-Hinweis

Der **target-check** prüft u. a. Mount-Quelle, Geräteklassifikation und (unter `/media`/`/run/media`) Traversierbarkeit. Ohne sicheres externes Ziel: **blockiert**, kein Backup-Start.

## Verwandte Dokumente

- `docs/backup/BACKUP_TARGET_POLICY_EN.md`
- `docs/knowledge-base/backup/BACKUP_TARGET_SELECTION.md`
- `docs/faq/BACKUP_RESTORE_FAQ_DE.md`
