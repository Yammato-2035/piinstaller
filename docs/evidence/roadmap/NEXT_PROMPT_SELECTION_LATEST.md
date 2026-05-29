# Next Prompt Selection

**selected_prompt_id:** `RESCUE_ISO_VM_BOOT_VALIDATION_PREP`

**Begründung:** Hybrid-ISO (`binary.hybrid.iso`) per SHA256, `file` und `isoinfo` verifiziert. Kein VM-/Boot-/USB-Nachweis — Rescue bleibt **yellow**, nicht full-green.

**Nicht als Nächstes:** USB-Write, Restore, erneuter Full-Build (optional nur zsync-Cleanup für grünen LB_EXIT).

JSON: `NEXT_PROMPT_SELECTION_LATEST.json`
