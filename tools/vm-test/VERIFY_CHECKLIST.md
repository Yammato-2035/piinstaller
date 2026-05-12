# Erfolgsprüfung nach Restore

Nach Boot von der wiederhergestellten **Systemplatte** im Gast prüfen:

- [ ] System bootet ohne Kernel-Panic / GRUB-Fehler
- [ ] Login möglich (z. B. `testuser` / `testpass`, falls so installiert)
- [ ] Datei vorhanden und lesbar: `/opt/setuphelfer-test/marker.txt`
- [ ] Datei vorhanden und lesbar: `/etc/setuphelfer-test.conf`
- [ ] Datei vorhanden und lesbar: `~/testdata/file.txt` (im Benutzer-Home, z. B. `testuser`)

```bash
sudo test -f /opt/setuphelfer-test/marker.txt && cat /opt/setuphelfer-test/marker.txt
sudo test -f /etc/setuphelfer-test.conf && cat /etc/setuphelfer-test.conf
test -f "$HOME/testdata/file.txt" && cat "$HOME/testdata/file.txt"
```

## Host-Logging

```bash
cd tools/vm-test
./scripts/09-collect-diagnostics.sh
```
