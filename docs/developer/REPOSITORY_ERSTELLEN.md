# Repository auf GitHub erstellen - Schnell

## Schritt-für-Schritt

1. **Gehe zu:** https://github.com/new

2. **Repository-Name:** `piinstaller` (oder `PI-Installer` - Groß-/Kleinschreibung beachten!)

3. **Beschreibung:** z.B. "Raspberry Pi Installer & Configuration Tool"

4. **Sichtbarkeit:** Public oder Private (deine Wahl)

5. **WICHTIG - Lass diese Checkboxen UNCHECKED:**
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license

   (Wir haben bereits Code lokal!)

6. **Klicke:** "Create repository"

7. **Nach dem Erstellen:** GitHub zeigt dir eine Seite mit Befehlen. **IGNORIERE diese** - wir haben den Code bereits!

8. **Dann führe aus:**
   ```bash
   cd /home/gabrielglienke/Documents/PI-Installer
   git push -u origin master
   ```

---

**Hinweis:** Stelle sicher, dass der Repository-Name **genau** `piinstaller` ist (wie im Remote konfiguriert), oder passe den Remote an, wenn du einen anderen Namen wählst.
