# 14 Boot1 vs Boot2 Reproducibility Comparison

**Boot1:** `20260807_221550`  
**Boot2:** `20260808_064943`  
**Classification:** `reproducible`  
**xorg_forensic_allowed:** false (Boot3 + Heuristik-Fix erforderlich)

## Software identity

| Item | Boot1 | Boot2 | Match |
|------|-------|-------|-------|
| Payload | 1.10.5.0 | 1.10.5.0 | True |
| SquashFS | `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51` | `c57c6fb8bccc7f353b3bebc06b9f6782038fef3473ab1b4f7c4d151cbd5bca51` | True |
| cmdline | identical profile flags | identical | True |

## TUI / Runtime

| Check | Boot1 | Boot2 |
|-------|-------|-------|
| console_owner | tui_owned | tui_owned |
| gui/startx/chromium | False/False/False | False/False/False |
| failed systemd | True | True |
| collector | ok | ok |
| hw baseline rc | 0 | 0 |

## GPU / Net / Storage flags

| Flag | Boot1 | Boot2 |
|------|-------|-------|
| amdgpu | True | True |
| eDP | True | True |
| mt7921e | True | True |
| r8169 | True | True |
| nvidia/nouveau loaded | False | False |

## Baseline Gate

| Field | Boot1 | Boot2 | Match |
|-------|-------|-------|-------|
| status | blocked | blocked | True |
| memory_status | immediate_issue_detected | immediate_issue_detected | True |
| cpu_status | immediate_issue_detected | immediate_issue_detected | True |
| gpu_status | immediate_issue_detected | immediate_issue_detected | True |
| storage_status | test_unavailable | test_unavailable | True |
| backup_allowed | True | True | True |
| restore_allowed | False | False | True |
| os_installation_allowed | False | False | True |
| gui_mode_allowed | False | False | True |

## MCE / MODE2 (reproduced)

Both boots contain informational MCE decoder line and MODE2 reset lines (see JSON).

## Verdict

`reproducible` — TUI-Pfad und Hardware-Sichtbarkeit reproduzierbar; Gate bleibt `partial`/Restore blockiert wegen derselben Heuristik-False-Positives → Phase 4 Audit als Nächstes.
