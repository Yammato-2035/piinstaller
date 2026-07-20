# 07 – USB Target Safety Audit

| Kriterium | Ist |
|-----------|-----|
| Kandidaten | **1** |
| Gerät | `/dev/sda` |
| TRAN | usb |
| RM/HOTPLUG | 1/1 |
| Modell | Ultra Line (Intenso) |
| Größe | 63333990400 B (~59G) |
| Labels | SETUPHELFER + SETUP_LOGS |
| Serial | 24111412110686 |
| Root-Gerät | `/dev/nvme1n1p2` — **nicht** USB |
| Status | **identifiziert eindeutig** |

Hinweis: `SETUP_LOGS` ist aktuell rw gemountet unter `/media/volker/SETUP_LOGS2`. ESP (sda1) war für Inventory RO und ist vor dem Updater ungemountet.
