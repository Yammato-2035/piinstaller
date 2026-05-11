# Rescue ISO — VM Test Safety Policy

## Rahmen

- Tests und der VM-Orchestrator sind für **virtuelle Maschinen** gedacht, nicht für produktive Hardware.
- **Keine** echten USB-Sticks, **keine** Durchreichung physischer Host-Datenträger an die VM als „Production-Disk“.
- **Keine** Mounts von Host-Systempartitionen (`/dev/nvme0n1` o. Ä.) in den automatisierten Runner-Pfaden.

## Netzwerk

- **NAT** zum Erreichen des Gast-Backends (z. B. `http://10.0.2.2:8000`) ist ausreichend und erwünscht.
- Keine Pflicht zur **Bridge** ins produktive Firmen-LAN.

## VM-Betrieb

- Vor wiederholbaren Tests **Snapshots** der VM anlegen und zurücksetzen.
- **Keine** persistente Gast-Platte standardmäßig nötig; Live-ISO reicht für Read-only-Validierung.

## Datenwrites

- Keine automatischen **Writes auf interne Datenträger** des Hosts oder simulierter „echter“ Zielplatten im Gast ohne separates Gate.
