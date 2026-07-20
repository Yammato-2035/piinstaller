# 11 – Repair Path Decision

## Primärer Pfad: **E – weitere Diagnose**

Begründung: Kein vollständiger PI-RS-TUI-AUTO-003-Lauf. H7 bleibt die führende *Arbeitshypothese* aus Vorarbeiten, ist aber **nicht** durch diesen Auftrag bestätigt.

### Nächster physischer Schritt (kein Code)

1. Stick erneut am MSI booten.
2. In GRUB **explizit** wählen: `Setuphelfer – TUI-Eingabediagnose (read-only)`  
   (nicht Default/GUI, Timeout nicht abwarten).
3. tty2-Assistenten vollständig durchlaufen, Evidence finalisieren.
4. Erneut: `STICK ZURÜCK – IMPORT STARTEN`

### Reparatur (noch nicht)

Kein Code, kein Payload, kein USB-Update, bis ein kompletter Diagnoselauf vorliegt.
