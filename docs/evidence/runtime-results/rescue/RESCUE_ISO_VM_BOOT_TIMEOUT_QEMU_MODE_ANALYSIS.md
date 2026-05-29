# QEMU-Modus-Analyse

| Modus | Ergebnis |
|-------|----------|
| A) `-serial stdio -display none` | 120s, **0** Bytes stdout — kein Signal |
| B) **`-nographic`** | 600s, **SeaBIOS, iPXE, ISOLINUX** sichtbar |
| C) grafisch (Operator) | Handoff für manuelle Beobachtung |
| D) KVM | `/dev/kvm` da, User **nicht** in `kvm` — keine Gruppenänderung |

**Empfehlung:** Folge-Smokes mit **`-nographic`** und längerem Timeout (≥600s); für Kernel/Live ggf. noch länger oder visueller Operator-Smoke.

JSON: `rescue_iso_vm_boot_timeout_qemu_mode_analysis_latest.json`
