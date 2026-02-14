# Projekt in einen Ordner „piinstaller“ umziehen

Damit Sie aus dem Verzeichnis „Software aus PI holen“ rauskommen, können Sie das Projekt in einen Ordner **piinstaller** verschieben (z. B. direkt unter `Dokumente`).

## 1. Ordner verschieben

**Variante A – Neuer Ort: `~/Dokumente/piinstaller`**

```bash
mv "/home/volker/Dokumente/Software aus PI holen/piinstaller" /home/volker/Dokumente/piinstaller
```

**Variante B – Neuer Ort: `~/piinstaller`**

```bash
mv "/home/volker/Dokumente/Software aus PI holen/piinstaller" /home/volker/piinstaller
```

Danach arbeiten Sie immer aus dem neuen Pfad, z. B.:

```bash
cd ~/Dokumente/piinstaller
# oder
cd ~/piinstaller
```

## 2. Nach dem Umzug

- **Desktop-Verknüpfungen:** Einmal im neuen Ordner ausführen:
  ```bash
  cd /home/volker/Dokumente/piinstaller   # bzw. Ihren gewählten Pfad
  bash scripts/desktop-launcher-alle-anlegen.sh
  ```
  Dann zeigen alle Starter auf den neuen Pfad.

- **systemd-Service:** Die Datei `pi-installer.service.install` ist bereits auf `/home/volker/Dokumente/piinstaller` vorkonfiguriert. Wenn Sie **Variante B** (`~/piinstaller`) gewählt haben, in der Datei den Pfad anpassen:
  ```bash
  sed -i 's|/home/volker/Dokumente/piinstaller|/home/volker/piinstaller|g' pi-installer.service.install
  ```
  Service neu einspielen:
  ```bash
  sudo cp pi-installer.service.install /etc/systemd/system/pi-installer.service
  sudo systemctl daemon-reload
  sudo systemctl restart pi-installer
  ```

- **Cursor/IDE:** Projekt im neuen Ordner öffnen („Open Folder“ → `~/Dokumente/piinstaller` oder `~/piinstaller`).

## 3. Alten Ordner löschen (optional)

Wenn unter „Software aus PI holen“ nur noch der (leere) Platz war und nichts anderes gebraucht wird:

```bash
rmdir "/home/volker/Dokumente/Software aus PI holen" 2>/dev/null || true
```

Wenn dort noch andere Dateien liegen, nur den Inhalt prüfen und den Ordner bei Bedarf behalten.
