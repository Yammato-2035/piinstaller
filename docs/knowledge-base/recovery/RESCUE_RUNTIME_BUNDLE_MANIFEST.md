# Rescue — Runtime Bundle Manifest & Seal (Strict)

## Kurzbeschreibung

Nach der Runtime-Assembly beschreibt diese Stufe den **Ist-Zustand** von `build/rescue/runtime/` als Inventar, legt Rohbyte-SHA256 je Datei ab, versiegelt die beiden JSON-Artefakte plus ein kanonisches Aggregat-Hash — **ohne** ISO, **ohne** Signatur-PKI.

## Ablauf

1. **Inventory:** Pflichtpfade (Verzeichnisse, Manifeste, Skripte), `.iso`/`.img`-Blocker, Symlink-Ziel unter `build/rescue`, Legacy in `.json`/`.sh`.
2. **Hash-Manifest:** Alle regulären Dateien unter `runtime/`, relative Pfade, Größen.
3. **Seal:** Nur bei Inventar/Hash `ok` oder `review_required`; `bundle_sha256` über `json.dumps(..., sort_keys=True, separators=(',', ':'))` des Hash-Manifest-Objekts.
4. **Consistency:** Liest Seal, prüft Datei-Hashes erneut, bindet Runtime-Assembly-Final-Gate und Safety-Handoff ein.

## Verwandt

- `docs/deploy/DEPLOY_RESCUE_RUNTIME_BUNDLE_MANIFEST_DE.md` / `_EN.md`
- Runner: `backend/deploy/runner_rescue_runtime_bundle_manifest.py`
