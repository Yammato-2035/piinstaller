# Frontend: REPO vs. RELEASE Trennung

Technische Trennung des Experten-Update-Moduls von der Release-Version im Frontend.

---

## Maßnahmen

### 1. Modusquelle

- **app_edition** kommt vom Backend über **/api/system-info** (und /api/init/status).
- In **App.tsx** wird `appEdition = systemInfo?.app_edition === 'repo' ? 'repo' : 'release'` abgeleitet (Default: release).
- Keine reine UI-Verstecklösung: Route und Menü sind an `appEdition` gekoppelt.

### 2. Navigation / Sidebar

- **Sidebar** erhält die Prop **appEdition**.
- Der Eintrag **„PI-Installer Update“** wird nur gerendert, wenn `appEdition === 'repo'` (Spread `...(appEdition === 'repo' ? [{ id: 'pi-installer-update', ... }] : [])`).
- In der **RELEASE-Version:** keine Sidebar-Verlinkung zum Expertenmodul.

### 3. Routen

- **App.tsx** `renderPage()`: Für `currentPage === 'pi-installer-update'` wird **nur bei `appEdition === 'repo'`** die Komponente **PiInstallerUpdate** gerendert.
- Bei **appEdition === 'release'** wird stattdessen das **Dashboard** gerendert (keine Expertenkarten, keine Build-Historie, keine DEB-Freigabe).
- Zusätzlich: **useEffect** leitet bei `appEdition === 'release'` und `currentPage === 'pi-installer-update'` auf **dashboard** um (`setCurrentPage('dashboard')`). Damit ist die Expertenseite in Release weder über Menü erreichbar noch über direkte URL dauerhaft sichtbar.

### 4. Expertenmodul-Inhalt (nur REPO)

- **PiInstallerUpdate** zeigt im REPO-Modus:
  - Self-Update-Status (Quelle, /opt, Deploy)
  - Expertenmodul „Update-Center“: Kompatibilität prüfen, DEB bauen, Release-Freigabe, Blocker, History
- Diese Komponente wird in der RELEASE-Version **nicht** gerendert; es werden keine Aufrufe zu /api/update-center/* ausgeführt (Route ist nicht anwählbar).

### 5. RELEASE: Benutzerseitige Alternative

- Die benutzerseitige Funktionalität (Zielsystem auswählen, Vorlagen/Presets/Images) bleibt über **Setup-Assistent (wizard)** und **Voreinstellungen (presets)** erreichbar.
- Kein eigener „Update“-Menüpunkt in Release; keine Entwicklertexte, keine Packaging-Sprache auf dieser Route.

---

## Betroffene Dateien

| Datei | Änderung |
|-------|----------|
| frontend/src/App.tsx | appEdition aus systemInfo; an Sidebar übergeben; case 'pi-installer-update' nur bei appEdition === 'repo' PiInstallerUpdate, sonst Dashboard; useEffect Redirect bei release + pi-installer-update |
| frontend/src/components/Sidebar.tsx | Prop appEdition; Menüeintrag „PI-Installer Update“ nur wenn appEdition === 'repo' |
| frontend/src/pages/PiInstallerUpdate.tsx | Unverändert; wird nur bei repo gerendert, ruft dann Update-Center-API auf |

---

## Sicherheit

- **Nicht nur CSS/hidden:** Route und Rendering sind an den Backend-Modus gebunden.
- Direkte URL `?page=pi-installer-update` in Release: Erst wird kurz Dashboard-Inhalt angezeigt (weil appEdition !== 'repo'), dann leitet der useEffect auf dashboard um.
