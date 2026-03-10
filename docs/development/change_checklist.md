# Change Checklist

_Kurze operative Checkliste für zukünftige Änderungen. Siehe auch `anti_regression_rules.md`._

---

## Vor jeder Änderung prüfen

- [ ] Gibt es bereits eine bestehende Funktion dafür?
- [ ] Gibt es bereits einen Helper/Service dafür?
- [ ] Gibt es dafür schon einen Config-Key?
- [ ] Gibt es dafür bereits Logging oder Debugging?
- [ ] Betrifft die Änderung Boot, Storage, Hardware oder Persistenz?
- [ ] Ist die Änderung für Grundlagen oder Erweitert gedacht?
- [ ] Werden bestehende Pfade, Links oder Menüeinträge ungültig?
- [ ] Verweist die Änderung auf Ziele, die existieren (API, Assets, Doku)?

---

## Vor jedem Commit / Abschlussschritt prüfen

- [ ] Keine doppelten Einträge erzeugt
- [ ] Keine alten Debug-Ausgaben hinterlassen (`print`, `console.*` im Produktivpfad)
- [ ] Keine toten Verweise erzeugt
- [ ] Keine zweite Implementierung eingeführt
- [ ] Keine Start-/Bootlogik unbeabsichtigt verändert
- [ ] Keine Expertenfunktion in den Basisteil gedrückt
- [ ] Keine neue Config ohne Prüfung bestehender Schlüssel

---

## Schnellreferenz: Kritische Pfade

| Thema | Datei(en) | Wichtig |
|-------|------------|---------|
| Haupt-Config | `backend/app.py` `_config_path()`, `_load_or_init_config()` | Nur `config.json` |
| Installer-Config | `scripts/install-system.sh`, `scripts/deploy-to-opt.sh` | Muss `config.json` erzeugen |
| Debug-Config | `backend/debug/config.py`, `debug.config.yaml` | ENV: `PIINSTALLER_DEBUG_*` |
| Start-Skripte | `start-backend.sh`, `pi-installer*.service` | Keine Änderung ohne Prüfung |
| API + Frontend | `backend/app.py` @app.*, `frontend/*Setup*.tsx` fetchApi | Endpunkt muss existieren |
