# GitHub Setup - Schnellanleitung

## 1. SSH-Key zu GitHub hinzufügen

Der öffentliche SSH-Key wurde bereits erstellt. **Füge ihn zu deinem GitHub-Account hinzu:**

1. Öffne: https://github.com/settings/keys
2. Klicke auf **"New SSH key"**
3. **Title:** z.B. "Raspberry Pi - PI-Installer"
4. **Key:** Kopiere diesen Key:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJt09YgRRrNZaYqbw2kJ356OCiwQ+qsaywiXA2JFUyIP github-pi-installer
```

5. Klicke **"Add SSH key"**

## 2. GitHub-Repository erstellen

1. Gehe zu: https://github.com/new
2. **Repository name:** z.B. `PI-Installer` oder `pi-installer`
3. **Description:** z.B. "Raspberry Pi Installer & Configuration Tool"
4. **Visibility:** Public oder Private (deine Wahl)
5. **WICHTIG:** Lass alle Checkboxen **unchecked** (kein README, keine .gitignore, keine License)
6. Klicke **"Create repository"**

## 3. Repository-URL notieren

Nach dem Erstellen zeigt GitHub dir die Repository-URL. Sie sieht so aus:
- **SSH:** `git@github.com:DEIN-USERNAME/REPO-NAME.git`
- **HTTPS:** `https://github.com/DEIN-USERNAME/REPO-NAME.git`

**Notiere dir diese URL!**

## 4. Verbindung testen

Nachdem du den SSH-Key zu GitHub hinzugefügt hast, teste die Verbindung:

```bash
ssh -T git@github.com
```

Du solltest sehen: `Hi DEIN-USERNAME! You've successfully authenticated...`

## 5. Remote hinzufügen und pushen

Sobald das Repository erstellt ist, führe diese Befehle aus (ersetze `DEIN-USERNAME/REPO-NAME`):

```bash
cd /home/gabrielglienke/Documents/PI-Installer
git remote add origin git@github.com:DEIN-USERNAME/REPO-NAME.git
git branch -M main  # Optional: Branch zu 'main' umbenennen
git push -u origin main  # oder 'master', je nach Branch-Name
```

---

**Falls du den GitHub-Benutzernamen und Repository-Namen bereits hast, kann ich die Befehle direkt ausführen!**
