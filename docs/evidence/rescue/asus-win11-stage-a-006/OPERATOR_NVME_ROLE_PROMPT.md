# Operator: NVMe-Rollenbindung (verbindlich)

Beide Samsung 970 EVO Plus 2TB / FW 2B2QEXM7 — **nicht** nach /dev/nvme* oder Disk-Nummer wählen.

| Feld | Laufwerk A (provisorisch Windows) | Laufwerk B (provisorisch Linux) |
|------|-----------------------------------|----------------------------------|
| Identity Hash | `6b45cc50d930d46e…` | `ed84d453078b002b…` |
| Serial masked | `…125Y` | `…241F` |
| EUI | `0025385a11b16304` | `0025385811911d10` |
| PCI | `0000:00:02.4` | `0000:00:02.3` |
| SMART (last capture) | WARNING, cw=0, me=0 | WARNING, cw=0, me=0 |

Bitte bestätigen: welches ist **Windows Target**, welches **Linux Target**.
Danach Isolation (physisch bevorzugt) und Stage A.
