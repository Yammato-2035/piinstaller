# Asset Mapping (SetupHelfer)

Dieses Mapping ordnet die neuen, konsistenten Assets den Bereichen im Theme zu.

## Branding-Assets (`assets/branding/`)
- Hauptlogo (Header/Website): `setuphelfer-logo-main.svg`
- Kompakte Wortmarke: `setuphelfer-wordmark-compact.svg`
- Signet (kleine Flaechen): `setuphelfer-signet.svg`
- Favicon: `setuphelfer-favicon.svg`
- App-nahes Icon (Download/Hero/Social Preview): `setuphelfer-app-icon.svg`

## A) Hero-Grafiken (`assets/hero/`)
1. Tux mit Linux-Laptop -> `hero-tux-linux-laptop.svg`
2. Raspberry Pi neben Desktop-PC -> `hero-pi-desktop.svg`
3. Raspberry Pi neben Laptop -> `hero-pi-laptop.svg`
4. Setup-Szene (Tux + Pi + Desktop/Laptop) -> `hero-setup-scene.svg`

Empfohlene Verwendung:
- Startseite Hero: `hero-setup-scene.svg`
- Download-Bereich: `hero-pi-desktop.svg` oder `hero-pi-laptop.svg`
- About/Community-Teaser: `hero-tux-linux-laptop.svg`

## B) Bereichsgrafiken (`assets/illustrations/`)
5. Geführter Einstieg -> `section-guided-start.svg`
6. Projekte entdecken -> `section-projects-discovery.svg`
7. Tutorials & Hilfe -> `section-tutorials-help.svg`
8. Community / Forum -> `section-community-forum.svg`
9. Sicherheit / geschütztes Setup -> `section-security-setup.svg`
10. Download / Installer -> `section-download-installer.svg`

## C) Projekt-Icons (`assets/icons/`)
11. Medienserver -> `project-media-server.svg`
12. Musikbox -> `project-musicbox.svg`
13. Backup -> `project-backup.svg`
14. Smart Home -> `project-smart-home.svg`
15. Retro Gaming -> `project-retro-gaming.svg`
16. Bilderrahmen -> `project-photo-frame.svg`
17. NAS / Dateiserver -> `project-nas-fileserver.svg`
18. Lernen / Programmieren -> `project-learning-coding.svg`

## D) Tutorial-Icons (`assets/icons/`)
19. Installation -> `tutorial-installation.svg`
20. Netzwerk -> `tutorial-network.svg`
21. Updates -> `tutorial-updates.svg`
22. Backup -> `tutorial-backup.svg`
23. Sicherheit -> `tutorial-security.svg`
24. Fehlerbehebung -> `tutorial-troubleshooting.svg`

## E) UI-/Funktionsicons (`assets/ui/`)
25. Suche -> `ui-search.svg`
26. Filter -> `ui-filter.svg`
27. Download -> `ui-download.svg`
28. Forum -> `ui-forum.svg`
29. Benutzerprofil -> `ui-user-profile.svg`
30. Fortschritt -> `ui-progress.svg`
31. Warnung -> `ui-warning.svg`
32. Hinweis -> `ui-info.svg`
33. Erfolg -> `ui-success.svg`
34. Einstellungen -> `ui-settings.svg`

## Integration im bestehenden Theme
- Bestehende Snippets koennen schrittweise von `assets/images/*` und `assets/icons/icon-*`
  auf die neuen Pfade umgestellt werden.
- Vorteil: keine harte Umstellung in einem einzigen Schritt, dadurch geringes Risiko.
