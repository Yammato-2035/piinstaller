# 01 – Implementation Input Audit

## Komponenten

| Komponente | Pfad | Status |
|------------|------|--------|
| Contract | `backend/core/rescue_tui_input_diagnostic_contract.py` | vorhanden |
| Main/CLI-Logik | `backend/core/rescue_tui_input_diagnostic.py` (+ evaluate/evdev/evidence/inventory) | vorhanden |
| Einstiegspunkt | `scripts/rescue-live/image/setuphelfer-rescue-tui-input-diagnostic` | ausführbar |
| systemd Unit | `…/systemd/setuphelfer-rescue-tui-input-diagnostic.service` | `ConditionKernelCommandLine=setuphelfer_tui_input_diag=1`, `TTYPath=/dev/tty2` |
| TUI Guard | `setuphelfer-rescue-tui.sh` | sperrt e2e/plan/gui/reboot/poweroff bei Diag-Flag |
| GRUB | `rescue_msi_lab_auto_boot.ensure_tui_input_diagnostic_menuentry` | Titel „TUI-Eingabediagnose (read-only)“, nicht Default |
| Inject | `scripts/rescue/inject-gui-bvr-fixes-into-stick-squashfs.sh` | CLI+Unit+alle `rescue_*.py`+Versionsträger im Squash |
| Import | `scripts/rescue/import-tui-input-diagnostic-runs.sh` | vorhanden |
| Tests | `backend/tests/test_rescue_tui_input_diagnostic_v1.py` | 38 Tests |

## Pflichtnachweise

- Diagnose **nur** über Kernelparameter `setuphelfer_tui_input_diag=1`.
- Unit auf **tty2**; normale TUI bleibt tty1.
- GRUB-Diagnoseeintrag **nicht** Default (`set default=0` bleibt GUI/Text-Lab).
- Auto-Shutdown Default: `setuphelfer_tui_input_diag_auto_shutdown=0`.
- Gefährliche TUI-Aktionen im Diagnosemodus gesperrt.
- Keine neue Runtime-Paketabhängigkeit (evdev optional/passiv, Standard-Python).
- Versionscarrier-Injection im Inject-Skript: VERSION + beide JSON im Squash.
