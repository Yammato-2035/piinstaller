# Rescue Remote — Development Control Center (DE)

## Tab „Rescue Remote“ (Konzept Phase 1)

### Anzeigen

- Gepaarte Agents, online/offline
- Netzwerkinterface, IP, letzter Heartbeat
- Capabilities (`run_write_runbooks: false`)
- Allowlisted Runbooks
- Job-Historie
- Copy Logs / Download Evidence (redigiert)
- Disconnect

### Erlaubte Aktionen

- Collect Boot Logs
- Collect Network Status
- Collect Storage Inventory (readonly)
- Test Devserver Connectivity
- Collect Agent Logs
- Disconnect

### Verboten (keine Buttons)

Shell, Run Command, Restore, Backup, USB Write, Mount RW, Format, Partition, apt install.
