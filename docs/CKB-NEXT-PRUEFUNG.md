# Prüfnotiz: `ckb-next`-Submodul (E-12)

> Faktische Bestandsaufnahme, keine Rechtsberatung. Bei Unklarheit vor
> Veröffentlichung anwaltlich prüfen lassen.

## Befund

- `.gitmodules` referenziert `ckb-next` als Git-Submodul, Quelle:
  `https://github.com/ckb-next/ckb-next.git`.
- Im öffentlichen ZIP-Export ist der Submodul-Ordner **leer** — es wird
  nur der Verweis (Commit-Pointer) versioniert, kein Quellcode oder Binary
  von `ckb-next` selbst liegt im Setuphelfer-Repository.
- Laut `docs/SYSTEM_AUDIT_REPORT.md` wird `ckb-next` im Projekt
  ausdrücklich **nicht als First-Party-Codebasis** behandelt, sondern nur
  dort berücksichtigt, wo es das Hauptrepo strukturell betrifft
  (Submodul-Referenz).
- `ckb-next` selbst steht unter **GPLv2** (Corsair-Tastatur-/Maustreiber,
  gebündelt mit einer QT-basierten GUI).

## Einordnung

**Solange** `ckb-next` nur als Submodul-Referenz im Repository steht und
nicht als kompiliertes Binary Teil des ausgelieferten Rescue-Stick-Images
wird, entsteht keine Distributionspflicht für Setuphelfer selbst — ihr
verteilt in diesem Fall keinen `ckb-next`-Code, sondern lediglich einen
Verweis darauf, den sich jeder selbst von GitHub holen kann.

**Kritisch wird es**, sobald `ckb-next` (kompiliert oder als Quellcode)
tatsächlich auf den Rescue Stick gepackt wird, damit z. B. Corsair-
Tastaturen im Live-System funktionieren. Dann greift GPLv2 für dieses
Binary: Wer es weitergibt, muss den (ggf. modifizierten) Quellcode von
`ckb-next` mitliefern oder auf Anfrage bereitstellen — unabhängig von der
Setuphelfer-eigenen Lizenz. Das beträfe nur die `ckb-next`-Komponente
selbst, nicht den Setuphelfer-Core (kein "Copyleft-Durchschlag" auf
euren Code, da es sich um ein separates, per Prozessgrenze getrenntes
Programm handelt — subprocess-artige Nutzung wie bei ClamAV/parted, nicht
Linking).

## Empfehlung

1. Prüfen, ob der aktuelle Rescue-Stick-Build (`live-build`-Pipeline)
   `ckb-next` tatsächlich einkompiliert. Falls ja: `ckb-next`-Quellcode
   (unverändert oder mit euren Patches) muss mit auf dem Stick oder über
   einen dokumentierten Bezugsweg verfügbar sein.
2. Falls `ckb-next` nur optional/dokumentiert als "kannst du selbst
   nachinstallieren" erwähnt wird, aber nicht mitgeliefert wird: unkritisch,
   keine weitere Maßnahme nötig.
3. Diese Prüfung bitte an den Senior-Linux-Admin oder Entwickler geben —
   das lässt sich nur am tatsächlichen Build-Output beantworten, nicht am
   Quellcode-Repository allein.
