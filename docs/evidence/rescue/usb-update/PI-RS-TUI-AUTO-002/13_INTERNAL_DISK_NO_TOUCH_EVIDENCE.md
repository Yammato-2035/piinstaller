# 13 – Internal Disk No-Touch Evidence

| Prüfung | Ergebnis |
|---------|----------|
| Root vorher/nachher | `/dev/nvme1n1p2` unverändert |
| Neue interne Partition | nein |
| Neuer interner Mount | nein |
| Updater-Ziel | nur `/dev/sda1` |
| SETUP_LOGS beschrieben | nein (Updater schreibt ESP) |
| nvme0n1 / nvme1n1 | unverändert in lsblk |
