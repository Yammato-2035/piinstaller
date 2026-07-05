"""Phase-1 translation marathon — glossary helpers (no external API)."""

from __future__ import annotations

import re
from typing import Iterable

# Longest phrases first when applying replacements.
EN_TO_FR: tuple[tuple[str, str], ...] = (
    ("Development Control Center", "Centre de contrôle du développement"),
    ("Backup and restore", "Sauvegarde et restauration"),
    ("Rescue stick", "Clé de secours"),
    ("Settings", "Paramètres"),
    ("Language", "Langue"),
    ("Refresh", "Actualiser"),
    ("Cancel", "Annuler"),
    ("Save", "Enregistrer"),
    ("Delete", "Supprimer"),
    ("Close", "Fermer"),
    ("Back", "Retour"),
    ("Next", "Suivant"),
    ("Previous", "Précédent"),
    ("Loading", "Chargement"),
    ("Error", "Erreur"),
    ("Warning", "Avertissement"),
    ("Success", "Succès"),
    ("Unknown", "Inconnu"),
    ("Yes", "Oui"),
    ("No", "Non"),
    ("Search", "Rechercher"),
    ("Documentation", "Documentation"),
    ("Diagnostics", "Diagnostics"),
    ("Deploy", "Déploiement"),
    ("Backup", "Sauvegarde"),
    ("Restore", "Restauration"),
    ("Network", "Réseau"),
    ("Partition", "Partition"),
    ("Device", "Périphérique"),
    ("External", "Externe"),
    ("Internal", "Interne"),
    ("Rescue", "Secours"),
    ("Linux", "Linux"),
    ("Windows", "Windows"),
    ("not available", "non disponible"),
    ("read-only", "lecture seule"),
    ("blocked", "bloqué"),
    ("green", "vert"),
    ("red", "rouge"),
    ("yellow", "jaune"),
)

EN_TO_NL: tuple[tuple[str, str], ...] = (
    ("Development Control Center", "Ontwikkelingscontrolecentrum"),
    ("Backup and restore", "Back-up en herstel"),
    ("Rescue stick", "Reddingsstick"),
    ("Settings", "Instellingen"),
    ("Language", "Taal"),
    ("Refresh", "Vernieuwen"),
    ("Cancel", "Annuleren"),
    ("Save", "Opslaan"),
    ("Delete", "Verwijderen"),
    ("Close", "Sluiten"),
    ("Back", "Terug"),
    ("Next", "Volgende"),
    ("Previous", "Vorige"),
    ("Loading", "Laden"),
    ("Error", "Fout"),
    ("Warning", "Waarschuwing"),
    ("Success", "Geslaagd"),
    ("Unknown", "Onbekend"),
    ("Yes", "Ja"),
    ("No", "Nee"),
    ("Search", "Zoeken"),
    ("Documentation", "Documentatie"),
    ("Diagnostics", "Diagnostiek"),
    ("Deploy", "Deploy"),
    ("Backup", "Back-up"),
    ("Restore", "Herstel"),
    ("Network", "Netwerk"),
    ("Partition", "Partitie"),
    ("Device", "Apparaat"),
    ("External", "Extern"),
    ("Internal", "Intern"),
    ("Rescue", "Redding"),
    ("Linux", "Linux"),
    ("Windows", "Windows"),
    ("not available", "niet beschikbaar"),
    ("read-only", "alleen-lezen"),
    ("blocked", "geblokkeerd"),
    ("green", "groen"),
    ("red", "rood"),
    ("yellow", "geel"),
)

DE_TO_EN: tuple[tuple[str, str], ...] = (
    ("Rettungsstick", "Rescue stick"),
    ("Datenträger", "Storage device"),
    ("Festplatte", "Disk"),
    ("Partition", "Partition"),
    ("Sicherung", "Backup"),
    ("Wiederherstellung", "Restore"),
    ("Einstellungen", "Settings"),
    ("Sprache", "Language"),
    ("Netzwerk", "Network"),
    ("Gerät", "Device"),
    ("extern", "external"),
    ("intern", "internal"),
    ("nicht verfügbar", "not available"),
    ("blockiert", "blocked"),
    ("Fehler", "Error"),
    ("Warnung", "Warning"),
    ("lädt", "loading"),
    ("Zurück", "Back"),
    ("Abbrechen", "Cancel"),
    ("Speichern", "Save"),
)

DE_TO_FR: tuple[tuple[str, str], ...] = (
    ("Rettungsstick", "Clé de secours"),
    ("Datenträger", "Périphérique de stockage"),
    ("Festplatte", "Disque"),
    ("Sicherung", "Sauvegarde"),
    ("Wiederherstellung", "Restauration"),
    ("Einstellungen", "Paramètres"),
    ("Sprache", "Langue"),
    ("Netzwerk", "Réseau"),
    ("Gerät", "Périphérique"),
    ("Zurück", "Retour"),
    ("Speichern", "Enregistrer"),
    ("Abbrechen", "Annuler"),
    ("Fehler", "Erreur"),
    ("Warnung", "Avertissement"),
    ("nicht verfügbar", "non disponible"),
    ("blockiert", "bloqué"),
    ("Bitte warten", "Veuillez patienter"),
    ("wird geladen", "chargement en cours"),
)

DE_TO_NL: tuple[tuple[str, str], ...] = (
    ("Rettungsstick", "Reddingsstick"),
    ("Datenträger", "Opslagmedium"),
    ("Festplatte", "Schijf"),
    ("Sicherung", "Back-up"),
    ("Wiederherstellung", "Herstel"),
    ("Einstellungen", "Instellingen"),
    ("Sprache", "Taal"),
    ("Netzwerk", "Netwerk"),
    ("Gerät", "Apparaat"),
    ("Zurück", "Terug"),
    ("Speichern", "Opslaan"),
    ("Abbrechen", "Annuleren"),
    ("Fehler", "Fout"),
    ("Warnung", "Waarschuwing"),
    ("nicht verfügbar", "niet beschikbaar"),
    ("blockiert", "geblokkeerd"),
    ("Bitte warten", "Even geduld"),
    ("wird geladen", "wordt geladen"),
)


def _apply_pairs(text: str, pairs: Iterable[tuple[str, str]]) -> str:
    out = text
    for src, dst in pairs:
        out = re.sub(re.escape(src), dst, out, flags=re.IGNORECASE)
    return out


def translate_en_to_fr(text: str) -> str:
    return _apply_pairs(text, EN_TO_FR)


def translate_en_to_nl(text: str) -> str:
    return _apply_pairs(text, EN_TO_NL)


def translate_de_to_en(text: str) -> str:
    return _apply_pairs(text, DE_TO_EN)


def translate_de_to_fr(text: str) -> str:
    return translate_en_to_fr(translate_de_to_en(text))


def translate_de_to_nl(text: str) -> str:
    return translate_en_to_nl(translate_de_to_en(text))


def doc_banner(target_lang: str, source_path: str) -> str:
    labels = {"DE": "Deutsch", "EN": "English", "FR": "Français", "NL": "Nederlands"}
    return (
        f"> **Phase-1 Übersetzungsmarathon** — {labels.get(target_lang, target_lang)} "
        f"(automatisch aus `{source_path}`). Bitte bei Release manuell gegenlesen.\n\n"
    )
