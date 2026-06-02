# Rescue ISO — dangerous_path_override Validator-Regel-Review

**Datum:** 2026-06-02  
**HEAD:** `11453c5`

## Regel-Ort

`scripts/rescue-live/validate-live-build-dpkg-preflight.sh` — aufgerufen von `validate-controlled-live-build-tree.sh`.

Exit **14** = `dangerous_path_override`.

## Scan-Logik (vor Fix)

```bash
grep -RInE 'PATH=|export PATH|env -i|dpkg|start-stop-daemon' \
  auto config/hooks config/includes.chroot/etc
```

## Befund

| Frage | Antwort |
|-------|---------|
| `/opt` pauschal verboten | **no** — Scan sucht PATH/dpkg-Overrides, nicht `/opt` generell |
| Allowlist-Mechanismus vor Fix | **no** |
| Unterscheidung Host vs. Live-Image | **no** — Scan behandelt includes.chroot/etc als Build-Tree-Inhalt |
| Unit-File-Kontext | **no** (vor Fix) |
| Tests vor Fix | **no** (neu: `test_rescue_iso_dangerous_path_validator_v1.py`) |
| False Positive für PYTHONPATH | **yes** — `PATH=` matchte Substring in `PYTHONPATH=` |

## Pflichtbewertung

| Frage | Antwort |
|-------|---------|
| Regel sinnvoll als Schutz gegen Hostpfad-/Write-Fehler | **yes** |
| False Positive für systemd Environment möglich | **yes** (PYTHONPATH) |
| Eng begrenzte Allowlist möglich | **yes** |
| Pauschales Freischalten von `/opt` erlaubt | **no** |
| Empfohlene Lösung | **`narrow_allowlist_for_systemd_environment_pythonpath`** + Regex-Fix `(^|[^A-Z_])PATH=` |

Evidence: `rescue_iso_validator_rule_occurrences_latest.log`
