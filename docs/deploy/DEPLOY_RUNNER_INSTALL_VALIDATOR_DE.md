# Deploy Runner Install Validator (Dry-run)

## Ziel

Read-only Validierung, ob ein Zielsystem fuer die spaetere manuelle Runner-Installation vorbereitet ist.

## Umfang

- Runner-Binary-Check (Existenz, Datei, Symlink, Parent-Permissions, Marker)
- Jobdirectory-Check (Existenz, Verzeichnis, Prefix, Symlink, Parent-Permissions)
- Snippet-Check nur gegen uebergebenen Text
- Environment-Check mit Boundary-/Sandbox-Audits
- Rollback-Pflichtschritte als Planvalidierung

## Wichtig

Keine Installation, keine Rechteaenderung, kein Schreiben in Systempfade.
